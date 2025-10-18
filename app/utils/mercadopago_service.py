import mercadopago
import logging
from flask import current_app
from app.utils.db import query_db

logger = logging.getLogger(__name__)

def get_mercadopago_sdk():
    """Retorna uma instância do SDK do Mercado Pago configurado"""
    config = query_db('SELECT mercadopago_access_token FROM configuracoes_loja WHERE id = 1', one=True)
    
    if not config or not config['mercadopago_access_token']:
        logger.error("Access Token do Mercado Pago não configurado")
        return None
    
    try:
        sdk = mercadopago.SDK(config['mercadopago_access_token'])
        return sdk
    except Exception as e:
        logger.error(f"Erro ao inicializar SDK do Mercado Pago: {e}")
        return None

def get_public_key():
    """Retorna a chave pública do Mercado Pago"""
    config = query_db('SELECT mercadopago_public_key FROM configuracoes_loja WHERE id = 1', one=True)
    
    if not config or not config['mercadopago_public_key']:
        return None
    
    return config['mercadopago_public_key']

def is_mercadopago_configured():
    """Verifica se o Mercado Pago está configurado"""
    config = query_db('SELECT mercadopago_access_token FROM configuracoes_loja WHERE id = 1', one=True)
    return config and config['mercadopago_access_token']

def create_payment_preference(pedido_id, items, payer_info, notification_url, back_urls):
    """
    Cria uma preferência de pagamento no Mercado Pago
    
    Args:
        pedido_id: ID do pedido no sistema
        items: Lista de items [{title, quantity, unit_price}]
        payer_info: Informações do pagador {email, name}
        notification_url: URL para receber notificações de webhook
        back_urls: URLs de retorno {success, failure, pending}
    
    Returns:
        dict com preference_id, init_point (URL de pagamento) ou None em caso de erro
    """
    sdk = get_mercadopago_sdk()
    
    if not sdk:
        logger.error("SDK do Mercado Pago não configurado")
        return None
    
    try:
        preference_data = {
            "items": items,
            "payer": {
                "name": payer_info.get('name', ''),
                "email": payer_info.get('email', '')
            },
            "back_urls": back_urls,
            "auto_return": "approved",
            "notification_url": notification_url,
            "external_reference": str(pedido_id),
            "statement_descriptor": "E-SHOP",
            "payment_methods": {
                "installments": 12
            }
        }
        
        logger.info(f"Criando preferência de pagamento para pedido {pedido_id}")
        preference_response = sdk.preference().create(preference_data)
        
        if preference_response["status"] == 201:
            preference = preference_response["response"]
            logger.info(f"Preferência criada com sucesso: {preference['id']}")
            return {
                "preference_id": preference["id"],
                "init_point": preference["init_point"],
                "sandbox_init_point": preference.get("sandbox_init_point")
            }
        else:
            logger.error(f"Erro ao criar preferência: {preference_response}")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao criar preferência de pagamento: {e}")
        return None

def get_payment_info(payment_id):
    """
    Obtém informações sobre um pagamento
    
    Args:
        payment_id: ID do pagamento no Mercado Pago
    
    Returns:
        dict com informações do pagamento ou None em caso de erro
    """
    sdk = get_mercadopago_sdk()
    
    if not sdk:
        logger.error("SDK do Mercado Pago não configurado")
        return None
    
    try:
        payment_info = sdk.payment().get(payment_id)
        
        if payment_info["status"] == 200:
            payment = payment_info["response"]
            return {
                "id": payment["id"],
                "status": payment["status"],
                "status_detail": payment.get("status_detail"),
                "transaction_amount": payment.get("transaction_amount"),
                "payment_method_id": payment.get("payment_method_id"),
                "payment_type_id": payment.get("payment_type_id"),
                "external_reference": payment.get("external_reference"),
                "payer_email": payment.get("payer", {}).get("email")
            }
        else:
            logger.error(f"Erro ao obter informações do pagamento: {payment_info}")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao obter informações do pagamento: {e}")
        return None

def get_payment_status_label(status):
    """
    Retorna uma label legível para o status do pagamento
    
    Args:
        status: Status do pagamento (approved, pending, rejected, etc)
    
    Returns:
        str com a label em português
    """
    status_map = {
        "approved": "Aprovado",
        "pending": "Pendente",
        "in_process": "Em processamento",
        "rejected": "Rejeitado",
        "cancelled": "Cancelado",
        "refunded": "Reembolsado",
        "charged_back": "Estornado"
    }
    return status_map.get(status, status.capitalize())

def is_payment_approved(status):
    """
    Verifica se o pagamento foi aprovado
    
    Args:
        status: Status do pagamento
    
    Returns:
        bool indicando se foi aprovado
    """
    return status == "approved"
