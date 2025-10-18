from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.utils.db import query_db, execute_db
from app.utils.decorators import login_required
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.helpers import save_image

customer_bp = Blueprint('customer', __name__, url_prefix='/minha-conta')

@customer_bp.route('/')
@login_required
def dashboard():
    user = query_db('SELECT * FROM usuarios WHERE id = ?', [session['user_id']], one=True)
    
    total_pedidos = query_db(
        'SELECT COUNT(*) as count FROM pedidos WHERE usuario_id = ?', 
        [session['user_id']], 
        one=True
    )['count']
    
    total_gasto = query_db(
        'SELECT COALESCE(SUM(total), 0) as total FROM pedidos WHERE usuario_id = ? AND status != ?', 
        [session['user_id'], 'cancelado'], 
        one=True
    )['total']
    
    pedidos_pendentes = query_db(
        'SELECT COUNT(*) as count FROM pedidos WHERE usuario_id = ? AND status = ?', 
        [session['user_id'], 'pendente'], 
        one=True
    )['count']
    
    pedidos_entregues = query_db(
        'SELECT COUNT(*) as count FROM pedidos WHERE usuario_id = ? AND status = ?', 
        [session['user_id'], 'entregue'], 
        one=True
    )['count']
    
    pedidos_recentes = query_db('''
        SELECT p.*, COUNT(pi.id) as total_itens
        FROM pedidos p
        LEFT JOIN pedido_itens pi ON p.id = pi.pedido_id
        WHERE p.usuario_id = ?
        GROUP BY p.id
        ORDER BY p.criado_em DESC
        LIMIT 5
    ''', [session['user_id']])
    
    return render_template('customer/dashboard.html',
                         user=user,
                         total_pedidos=total_pedidos,
                         total_gasto=total_gasto,
                         pedidos_pendentes=pedidos_pendentes,
                         pedidos_entregues=pedidos_entregues,
                         pedidos_recentes=pedidos_recentes)

@customer_bp.route('/pedidos')
@login_required
def pedidos():
    status_filter = request.args.get('status', '')
    
    query = '''
        SELECT p.*, COUNT(pi.id) as total_itens
        FROM pedidos p
        LEFT JOIN pedido_itens pi ON p.id = pi.pedido_id
        WHERE p.usuario_id = ?
    '''
    
    params = [session['user_id']]
    
    if status_filter:
        query += ' AND p.status = ?'
        params.append(status_filter)
    
    query += ' GROUP BY p.id ORDER BY p.criado_em DESC'
    
    pedidos = query_db(query, params)
    
    return render_template('customer/pedidos.html', pedidos=pedidos, status_filter=status_filter)

@customer_bp.route('/pedidos/<int:id>')
@login_required
def pedido_detalhes(id):
    pedido = query_db('''
        SELECT p.*
        FROM pedidos p
        WHERE p.id = ? AND p.usuario_id = ?
    ''', [id, session['user_id']], one=True)
    
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('customer.pedidos'))
    
    itens = query_db('''
        SELECT pi.*, pr.nome as produto_nome, pr.sku,
               (SELECT caminho_imagem FROM produto_imagens WHERE produto_id = pr.id ORDER BY ordem LIMIT 1) as imagem_principal
        FROM pedido_itens pi
        JOIN produtos pr ON pi.produto_id = pr.id
        WHERE pi.pedido_id = ?
    ''', [id])
    
    return render_template('customer/pedido_detalhes.html', pedido=pedido, itens=itens)

@customer_bp.route('/pedidos/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar_pedido(id):
    pedido = query_db('''
        SELECT * FROM pedidos 
        WHERE id = ? AND usuario_id = ? AND status = ?
    ''', [id, session['user_id'], 'pendente'], one=True)
    
    if not pedido:
        flash('Pedido não pode ser cancelado.', 'danger')
        return redirect(url_for('customer.pedidos'))
    
    itens = query_db('''
        SELECT produto_id, quantidade 
        FROM pedido_itens 
        WHERE pedido_id = ?
    ''', [id])
    
    for item in itens:
        execute_db('''
            UPDATE produtos 
            SET quantidade_estoque = quantidade_estoque + ?
            WHERE id = ?
        ''', (item['quantidade'], item['produto_id']))
    
    execute_db('''
        UPDATE pedidos 
        SET status = ?, atualizado_em = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', ['cancelado', id])
    
    flash('Pedido cancelado com sucesso! O estoque foi reajustado.', 'success')
    return redirect(url_for('customer.pedido_detalhes', id=id))

@customer_bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    user = query_db('SELECT * FROM usuarios WHERE id = ?', [session['user_id']], one=True)
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        
        foto_path = user['foto_perfil']
        if 'foto_perfil' in request.files:
            file = request.files['foto_perfil']
            if file and file.filename:
                foto_path = save_image(file, 'profiles', max_size=(300, 300))
        
        execute_db('''
            UPDATE usuarios 
            SET nome = ?, telefone = ?, foto_perfil = ?, atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (nome, telefone, foto_path, session['user_id']))
        
        session['user_name'] = nome
        session['user_photo'] = foto_path
        
        flash('Informações atualizadas com sucesso!', 'success')
        return redirect(url_for('customer.configuracoes'))
    
    return render_template('customer/configuracoes.html', user=user)

@customer_bp.route('/alterar-senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        user = query_db('SELECT senha_hash FROM usuarios WHERE id = ?', [session['user_id']], one=True)
        
        if not check_password_hash(user['senha_hash'], senha_atual):
            flash('Senha atual incorreta.', 'danger')
            return render_template('customer/alterar_senha.html')
        
        if nova_senha != confirmar_senha:
            flash('As senhas não coincidem.', 'danger')
            return render_template('customer/alterar_senha.html')
        
        if len(nova_senha) < 6:
            flash('A nova senha deve ter no mínimo 6 caracteres.', 'danger')
            return render_template('customer/alterar_senha.html')
        
        nova_senha_hash = generate_password_hash(nova_senha)
        execute_db('UPDATE usuarios SET senha_hash = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?', 
                   (nova_senha_hash, session['user_id']))
        
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('customer.dashboard'))
    
    return render_template('customer/alterar_senha.html')
