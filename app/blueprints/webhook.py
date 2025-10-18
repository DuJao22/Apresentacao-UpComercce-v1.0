from flask import Blueprint, request, jsonify
from app.utils.db import query_db, execute_db
from app.utils import mercadopago_service
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhook', __name__, url_prefix='/webhook')

def validate_mercadopago_signature(x_signature, x_request_id, data_id, secret):
    """
    Valida a assinatura do webhook do Mercado Pago
    
    Args:
        x_signature: Valor do header x-signature (formato: "ts=123456,v1=abc...")
        x_request_id: Valor do header x-request-id
        data_id: ID do pagamento/recurso dos query params
        secret: Chave secreta do webhook do Mercado Pago
    
    Returns:
        bool: True se a assinatura for válida
    """
    if not all([x_signature, x_request_id, data_id, secret]):
        logger.warning("Parâmetros de validação incompletos")
        return False
    
    try:
        parts = x_signature.split(',')
        if len(parts) != 2:
            logger.warning(f"Formato de assinatura inválido: {x_signature}")
            return False
        
        ts_part = parts[0]
        signature_part = parts[1]
        
        timestamp = ts_part.split('=')[1]
        received_signature = signature_part.split('=')[1]
        
        manifest = f"id:{data_id};request-id:{x_request_id};ts:{timestamp};"
        
        computed_signature = hmac.new(
            secret.encode('utf-8'),
            manifest.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        is_valid = hmac.compare_digest(received_signature, computed_signature)
        
        if not is_valid:
            logger.warning(f"Assinatura inválida. Esperado: {computed_signature}, Recebido: {received_signature}")
        
        return is_valid
        
    except (IndexError, AttributeError) as e:
        logger.error(f"Erro ao validar assinatura: {e}")
        return False

@webhook_bp.route('/mercadopago', methods=['POST'])
def mercadopago_webhook():
    """
    Webhook do Mercado Pago para receber notificações de pagamento
    Implementa validação de assinatura para segurança
    """
    try:
        config = query_db('SELECT mercadopago_webhook_secret FROM configuracoes_loja WHERE id = 1', one=True)
        webhook_secret = config['mercadopago_webhook_secret'] if config else None
        
        if webhook_secret:
            x_signature = request.headers.get('x-signature', '')
            x_request_id = request.headers.get('x-request-id', '')
            data_id = request.args.get('data.id', '')
            
            if not validate_mercadopago_signature(x_signature, x_request_id, data_id, webhook_secret):
                logger.warning("Tentativa de webhook com assinatura inválida rejeitada")
                return jsonify({"status": "error", "message": "Invalid signature"}), 401
        else:
            logger.warning("Webhook secret não configurado - validação de assinatura desabilitada")
        
        data = request.get_json()
        
        if not data:
            logger.warning("Webhook recebido sem dados")
            return jsonify({"status": "error", "message": "No data"}), 400
        
        logger.info(f"Webhook Mercado Pago recebido: {data}")
        
        notification_type = data.get('type')
        
        if notification_type == 'payment':
            payment_id = data.get('data', {}).get('id')
            
            if not payment_id:
                logger.warning("Payment ID não encontrado no webhook")
                return jsonify({"status": "error", "message": "No payment ID"}), 400
            
            payment_info = mercadopago_service.get_payment_info(payment_id)
            
            if not payment_info:
                logger.error(f"Erro ao obter informações do pagamento {payment_id}")
                return jsonify({"status": "error", "message": "Failed to get payment info"}), 500
            
            external_reference = payment_info.get('external_reference')
            
            if not external_reference:
                logger.warning(f"External reference não encontrado para pagamento {payment_id}")
                return jsonify({"status": "ok"}), 200
            
            pedido = query_db('SELECT * FROM pedidos WHERE id = ?', [external_reference], one=True)
            
            if not pedido:
                logger.warning(f"Pedido {external_reference} não encontrado")
                return jsonify({"status": "ok"}), 200
            
            status = payment_info.get('status')
            
            novo_status_pedido = pedido['status']
            if mercadopago_service.is_payment_approved(status):
                novo_status_pedido = 'pago'
            elif status in ['pending', 'in_process']:
                novo_status_pedido = 'pendente'
            elif status in ['rejected', 'cancelled']:
                novo_status_pedido = 'cancelado'
            
            execute_db('''
                UPDATE pedidos 
                SET mercadopago_payment_id = ?, status = ?, atualizado_em = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (payment_id, novo_status_pedido, external_reference))
            
            logger.info(f"Pedido {external_reference} atualizado: {novo_status_pedido} (Payment: {payment_id})")
            
            return jsonify({"status": "ok"}), 200
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook do Mercado Pago: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
