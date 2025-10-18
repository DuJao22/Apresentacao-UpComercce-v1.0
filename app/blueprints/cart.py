from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.utils.db import query_db, execute_db
from app.utils.decorators import login_required
from app.utils import mercadopago_service
import os

cart_bp = Blueprint('cart', __name__, url_prefix='/carrinho')

@cart_bp.route('/')
def index():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for product_id, item in cart.items():
        produto = query_db('''
            SELECT p.*, 
                   (SELECT caminho_imagem FROM produto_imagens WHERE produto_id = p.id ORDER BY ordem LIMIT 1) as imagem_principal
            FROM produtos p
            WHERE p.id = ?
        ''', [product_id], one=True)
        
        if produto:
            subtotal = produto['preco'] * item['quantity']
            cart_items.append({
                'produto': produto,
                'quantity': item['quantity'],
                'subtotal': subtotal
            })
            total += subtotal
    
    return render_template('shop/cart.html', cart_items=cart_items, total=total)

@cart_bp.route('/adicionar', methods=['POST'])
def adicionar():
    product_id = request.form.get('product_id')
    
    if not product_id:
        flash('Produto inválido.', 'danger')
        return redirect(url_for('shop.index'))
    
    try:
        quantity = int(request.form.get('quantity', 1))
    except (ValueError, TypeError):
        flash('Quantidade inválida.', 'danger')
        return redirect(url_for('shop.index'))
    
    if quantity < 1:
        flash('Quantidade deve ser maior que zero.', 'danger')
        return redirect(url_for('shop.index'))
    
    produto = query_db('SELECT * FROM produtos WHERE id = ? AND ativo = 1', [product_id], one=True)
    
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('shop.index'))
    
    cart = session.get('cart', {})
    
    quantidade_atual_carrinho = cart.get(product_id, {}).get('quantity', 0)
    quantidade_total = quantidade_atual_carrinho + quantity
    
    if produto['quantidade_estoque'] < quantidade_total:
        flash(f'Quantidade indisponível em estoque. Disponível: {produto["quantidade_estoque"]} unidades.', 'danger')
        return redirect(url_for('shop.produto', id=product_id))
    
    if product_id in cart:
        cart[product_id]['quantity'] += quantity
    else:
        cart[product_id] = {'quantity': quantity}
    
    session['cart'] = cart
    flash(f'{produto["nome"]} adicionado ao carrinho!', 'success')
    return redirect(url_for('shop.produto', id=product_id))

@cart_bp.route('/atualizar', methods=['POST'])
def atualizar():
    product_id = request.form.get('product_id')
    
    if not product_id:
        flash('Produto inválido.', 'danger')
        return redirect(url_for('cart.index'))
    
    try:
        quantity = int(request.form.get('quantity', 1))
    except (ValueError, TypeError):
        flash('Quantidade inválida.', 'danger')
        return redirect(url_for('cart.index'))
    
    cart = session.get('cart', {})
    
    if quantity > 0:
        produto = query_db('SELECT quantidade_estoque FROM produtos WHERE id = ?', [product_id], one=True)
        if produto and produto['quantidade_estoque'] >= quantity:
            cart[product_id]['quantity'] = quantity
        else:
            flash('Quantidade indisponível em estoque.', 'danger')
    else:
        if product_id in cart:
            del cart[product_id]
    
    session['cart'] = cart
    return redirect(url_for('cart.index'))

@cart_bp.route('/remover/<product_id>')
def remover(product_id):
    cart = session.get('cart', {})
    if product_id in cart:
        del cart[product_id]
        session['cart'] = cart
        flash('Item removido do carrinho.', 'info')
    return redirect(url_for('cart.index'))

@cart_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = session.get('cart', {})
    
    if not cart:
        flash('Seu carrinho está vazio.', 'warning')
        return redirect(url_for('shop.index'))
    
    if request.method == 'POST':
        tipo_entrega = request.form.get('tipo_entrega', 'entrega')
        endereco = request.form.get('endereco', '')
        metodo_pagamento = request.form.get('metodo_pagamento')
        observacoes = request.form.get('observacoes', '')
        
        if not metodo_pagamento:
            flash('Por favor, selecione um método de pagamento.', 'danger')
            return redirect(url_for('cart.checkout'))
        
        if tipo_entrega == 'entrega' and not endereco.strip():
            flash('Por favor, informe o endereço de entrega.', 'danger')
            return redirect(url_for('cart.checkout'))
        
        total = 0
        produtos_validos = []
        
        for product_id, item in cart.items():
            produto = query_db('SELECT * FROM produtos WHERE id = ? AND ativo = 1', [product_id], one=True)
            if produto:
                if produto['quantidade_estoque'] < item['quantity']:
                    flash(f'Produto {produto["nome"]} sem estoque suficiente. Disponível: {produto["quantidade_estoque"]} unidades.', 'danger')
                    return redirect(url_for('cart.index'))
                total += produto['preco'] * item['quantity']
                produtos_validos.append((product_id, item, produto))
            else:
                flash(f'Produto ID {product_id} não está mais disponível.', 'warning')
                if product_id in cart:
                    del cart[product_id]
                    session['cart'] = cart
                return redirect(url_for('cart.index'))
        
        if total <= 0:
            flash('Erro ao calcular o total do pedido.', 'danger')
            return redirect(url_for('cart.index'))
        
        try:
            pedido_id = execute_db('''
                INSERT INTO pedidos (usuario_id, total, status, metodo_pagamento, endereco_entrega, observacoes, tipo_entrega)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], total, 'pendente', metodo_pagamento, endereco, observacoes, tipo_entrega))
            
            for product_id, item, produto in produtos_validos:
                subtotal = produto['preco'] * item['quantity']
                execute_db('''
                    INSERT INTO pedido_itens (pedido_id, produto_id, quantidade, preco_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                ''', (pedido_id, product_id, item['quantity'], produto['preco'], subtotal))
                
                execute_db('''
                    UPDATE produtos 
                    SET quantidade_estoque = quantidade_estoque - ?, atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (item['quantity'], product_id))
            
            if metodo_pagamento == 'mercadopago' and mercadopago_service.is_mercadopago_configured():
                usuario = query_db('SELECT nome, email FROM usuarios WHERE id = ?', [session['user_id']], one=True)
                
                items = []
                for product_id, item, produto in produtos_validos:
                    items.append({
                        "title": produto['nome'],
                        "quantity": item['quantity'],
                        "unit_price": float(produto['preco']),
                        "currency_id": "BRL"
                    })
                
                domain = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
                base_url = f"https://{domain}" if domain != 'localhost:5000' else 'http://localhost:5000'
                
                back_urls = {
                    "success": f"{base_url}/carrinho/pagamento/sucesso?pedido_id={pedido_id}",
                    "failure": f"{base_url}/carrinho/pagamento/falha?pedido_id={pedido_id}",
                    "pending": f"{base_url}/carrinho/pagamento/pendente?pedido_id={pedido_id}"
                }
                
                notification_url = f"{base_url}/webhook/mercadopago"
                
                preference = mercadopago_service.create_payment_preference(
                    pedido_id=pedido_id,
                    items=items,
                    payer_info={
                        "name": usuario['nome'],
                        "email": usuario['email']
                    },
                    notification_url=notification_url,
                    back_urls=back_urls
                )
                
                if preference:
                    execute_db('''
                        UPDATE pedidos 
                        SET mercadopago_preference_id = ?
                        WHERE id = ?
                    ''', (preference['preference_id'], pedido_id))
                    
                    session.pop('cart', None)
                    return redirect(preference['init_point'])
                else:
                    flash('Erro ao inicializar pagamento com Mercado Pago. Tente novamente.', 'danger')
                    return redirect(url_for('cart.checkout'))
                    
        except Exception as e:
            flash('Erro ao processar pedido. Tente novamente.', 'danger')
            return redirect(url_for('cart.checkout'))
        
        session.pop('cart', None)
        flash('Pedido realizado com sucesso!', 'success')
        return redirect(url_for('customer.pedidos'))
    
    cart_items = []
    total = 0
    
    for product_id, item in cart.items():
        produto = query_db('SELECT * FROM produtos WHERE id = ?', [product_id], one=True)
        if produto:
            subtotal = produto['preco'] * item['quantity']
            cart_items.append({
                'produto': produto,
                'quantity': item['quantity'],
                'subtotal': subtotal
            })
            total += subtotal
    
    config = query_db('SELECT local_retirada, mercadopago_access_token FROM configuracoes_loja WHERE id = 1', one=True)
    local_retirada = config['local_retirada'] if config and config['local_retirada'] else None
    mercadopago_configurado = mercadopago_service.is_mercadopago_configured()
    
    return render_template('shop/checkout.html', cart_items=cart_items, total=total, 
                         local_retirada=local_retirada, mercadopago_configurado=mercadopago_configurado)

@cart_bp.route('/pagamento/sucesso')
@login_required
def pagamento_sucesso():
    pedido_id = request.args.get('pedido_id')
    payment_id = request.args.get('payment_id')
    
    if pedido_id:
        pedido = query_db('SELECT * FROM pedidos WHERE id = ? AND usuario_id = ?', 
                         [pedido_id, session['user_id']], one=True)
        
        if pedido:
            if payment_id:
                execute_db('''
                    UPDATE pedidos 
                    SET mercadopago_payment_id = ?, status = 'pago', atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (payment_id, pedido_id))
            
            flash('Pagamento realizado com sucesso! Obrigado pela sua compra.', 'success')
        else:
            flash('Pedido não encontrado.', 'warning')
    
    return redirect(url_for('customer.pedidos'))

@cart_bp.route('/pagamento/falha')
@login_required
def pagamento_falha():
    pedido_id = request.args.get('pedido_id')
    
    if pedido_id:
        pedido = query_db('SELECT * FROM pedidos WHERE id = ? AND usuario_id = ?', 
                         [pedido_id, session['user_id']], one=True)
        
        if pedido:
            flash('Pagamento não foi aprovado. Por favor, tente novamente ou escolha outro método de pagamento.', 'danger')
        else:
            flash('Pedido não encontrado.', 'warning')
    
    return redirect(url_for('customer.pedidos'))

@cart_bp.route('/pagamento/pendente')
@login_required
def pagamento_pendente():
    pedido_id = request.args.get('pedido_id')
    
    if pedido_id:
        pedido = query_db('SELECT * FROM pedidos WHERE id = ? AND usuario_id = ?', 
                         [pedido_id, session['user_id']], one=True)
        
        if pedido:
            flash('Seu pagamento está sendo processado. Você será notificado quando for aprovado.', 'info')
        else:
            flash('Pedido não encontrado.', 'warning')
    
    return redirect(url_for('customer.pedidos'))
