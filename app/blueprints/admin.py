from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response, jsonify
from werkzeug.security import generate_password_hash
from app.utils.db import query_db, execute_db, get_db
from app.utils.helpers import save_image, format_currency
from app.utils.decorators import admin_required
import csv
from io import StringIO
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def dashboard():
    total_usuarios = query_db('SELECT COUNT(*) as count FROM usuarios WHERE perfil = "cliente"', one=True)['count']
    total_produtos = query_db('SELECT COUNT(*) as count FROM produtos WHERE ativo = 1', one=True)['count']
    total_pedidos = query_db('SELECT COUNT(*) as count FROM pedidos', one=True)['count']
    total_vendido = query_db('SELECT COALESCE(SUM(total), 0) as total FROM pedidos WHERE status != "cancelado"', one=True)['total']
    
    pedidos_recentes = query_db('''
        SELECT p.*, u.nome as cliente_nome, COUNT(pi.id) as total_itens
        FROM pedidos p
        JOIN usuarios u ON p.usuario_id = u.id
        LEFT JOIN pedido_itens pi ON p.id = pi.pedido_id
        GROUP BY p.id
        ORDER BY p.criado_em DESC
        LIMIT 10
    ''')
    
    produtos_baixo_estoque = query_db('''
        SELECT p.*, c.nome as categoria_nome
        FROM produtos p
        JOIN categorias c ON p.categoria_id = c.id
        WHERE p.quantidade_estoque < 10 AND p.ativo = 1
        ORDER BY p.quantidade_estoque
        LIMIT 10
    ''')
    
    return render_template('admin/dashboard.html', 
                         total_usuarios=total_usuarios,
                         total_produtos=total_produtos,
                         total_pedidos=total_pedidos,
                         total_vendido=total_vendido,
                         pedidos_recentes=pedidos_recentes,
                         produtos_baixo_estoque=produtos_baixo_estoque)

@admin_bp.route('/usuarios')
@admin_required
def usuarios():
    usuarios = query_db('SELECT * FROM usuarios ORDER BY criado_em DESC')
    return render_template('admin/usuarios.html', usuarios=usuarios)

@admin_bp.route('/usuarios/<int:id>/resetar-senha', methods=['POST'])
@admin_required
def resetar_senha(id):
    nova_senha = request.form.get('nova_senha')
    
    if not nova_senha or len(nova_senha) < 6:
        flash('A nova senha deve ter pelo menos 6 caracteres.', 'danger')
        return redirect(url_for('admin.usuarios'))
    
    senha_hash = generate_password_hash(nova_senha)
    
    execute_db('UPDATE usuarios SET senha_hash = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?', 
               (senha_hash, id))
    
    execute_db('INSERT INTO logs_admin (usuario_id, acao, detalhes) VALUES (?, ?, ?)',
               (session['user_id'], 'reset_senha', f'Resetou senha do usuário ID {id}'))
    
    flash('Senha resetada com sucesso!', 'success')
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/<int:id>/toggle-status', methods=['POST'])
@admin_required
def toggle_usuario_status(id):
    usuario = query_db('SELECT ativo FROM usuarios WHERE id = ?', [id], one=True)
    novo_status = 0 if usuario['ativo'] else 1
    
    execute_db('UPDATE usuarios SET ativo = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?', 
               (novo_status, id))
    
    status_text = 'ativado' if novo_status else 'desativado'
    execute_db('INSERT INTO logs_admin (usuario_id, acao, detalhes) VALUES (?, ?, ?)',
               (session['user_id'], 'toggle_usuario', f'Usuário ID {id} {status_text}'))
    
    flash(f'Usuário {status_text} com sucesso!', 'success')
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/categorias', methods=['GET', 'POST'])
@admin_required
def categorias():
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        
        if not nome:
            flash('Nome da categoria é obrigatório.', 'danger')
            categorias = query_db('SELECT * FROM categorias ORDER BY nome')
            return render_template('admin/categorias.html', categorias=categorias)
        
        slug = nome.lower().replace(' ', '-').replace('ã', 'a').replace('õ', 'o').replace('ç', 'c')
        
        execute_db('INSERT INTO categorias (nome, descricao, slug) VALUES (?, ?, ?)', 
                   (nome, descricao, slug))
        
        execute_db('INSERT INTO logs_admin (usuario_id, acao, detalhes) VALUES (?, ?, ?)',
                   (session['user_id'], 'criar_categoria', f'Categoria "{nome}" criada'))
        
        flash('Categoria criada com sucesso!', 'success')
        return redirect(url_for('admin.categorias'))
    
    categorias = query_db('SELECT * FROM categorias ORDER BY nome')
    return render_template('admin/categorias.html', categorias=categorias)

@admin_bp.route('/categorias/<int:id>/toggle-status', methods=['POST'])
@admin_required
def toggle_categoria_status(id):
    categoria = query_db('SELECT ativo, nome FROM categorias WHERE id = ?', [id], one=True)
    novo_status = 0 if categoria['ativo'] else 1
    
    execute_db('UPDATE categorias SET ativo = ? WHERE id = ?', (novo_status, id))
    
    status_text = 'ativada' if novo_status else 'desativada'
    execute_db('INSERT INTO logs_admin (usuario_id, acao, detalhes) VALUES (?, ?, ?)',
               (session['user_id'], 'toggle_categoria', f'Categoria "{categoria["nome"]}" {status_text}'))
    
    flash(f'Categoria {status_text} com sucesso!', 'success')
    return redirect(url_for('admin.categorias'))

@admin_bp.route('/produtos', methods=['GET', 'POST'])
@admin_required
def produtos():
    if request.method == 'POST':
        categoria_id = request.form.get('categoria_id')
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        sku = request.form.get('sku')
        peso = request.form.get('peso') or None
        dimensoes = request.form.get('dimensoes') or None
        marca = request.form.get('marca') or None
        
        if not nome or not sku or not categoria_id:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            categorias = query_db('SELECT * FROM categorias WHERE ativo = 1 ORDER BY nome')
            produtos = query_db('''
                SELECT p.*, c.nome as categoria_nome,
                       (SELECT caminho_imagem FROM produto_imagens WHERE produto_id = p.id ORDER BY ordem LIMIT 1) as imagem_principal
                FROM produtos p
                JOIN categorias c ON p.categoria_id = c.id
                ORDER BY p.criado_em DESC
            ''')
            return render_template('admin/produtos.html', produtos=produtos, categorias=categorias)
        
        try:
            preco = float(request.form.get('preco'))
            if preco < 0:
                raise ValueError("Preço não pode ser negativo")
        except (ValueError, TypeError):
            flash('Preço inválido. Insira um número válido.', 'danger')
            categorias = query_db('SELECT * FROM categorias WHERE ativo = 1 ORDER BY nome')
            produtos = query_db('''
                SELECT p.*, c.nome as categoria_nome,
                       (SELECT caminho_imagem FROM produto_imagens WHERE produto_id = p.id ORDER BY ordem LIMIT 1) as imagem_principal
                FROM produtos p
                JOIN categorias c ON p.categoria_id = c.id
                ORDER BY p.criado_em DESC
            ''')
            return render_template('admin/produtos.html', produtos=produtos, categorias=categorias)
        
        try:
            quantidade_estoque = int(request.form.get('quantidade_estoque'))
            if quantidade_estoque < 0:
                raise ValueError("Quantidade não pode ser negativa")
        except (ValueError, TypeError):
            flash('Quantidade em estoque inválida. Insira um número inteiro válido.', 'danger')
            categorias = query_db('SELECT * FROM categorias WHERE ativo = 1 ORDER BY nome')
            produtos = query_db('''
                SELECT p.*, c.nome as categoria_nome,
                       (SELECT caminho_imagem FROM produto_imagens WHERE produto_id = p.id ORDER BY ordem LIMIT 1) as imagem_principal
                FROM produtos p
                JOIN categorias c ON p.categoria_id = c.id
                ORDER BY p.criado_em DESC
            ''')
            return render_template('admin/produtos.html', produtos=produtos, categorias=categorias)
        
        produto_id = execute_db('''
            INSERT INTO produtos (categoria_id, nome, descricao, preco, sku, quantidade_estoque, peso, dimensoes, marca)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (categoria_id, nome, descricao, preco, sku, quantidade_estoque, peso, dimensoes, marca))
        
        for i in range(1, 6):
            file_key = f'imagem_{i}'
            if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename:
                    image_path = save_image(file, 'products')
                    if image_path:
                        execute_db('''
                            INSERT INTO produto_imagens (produto_id, caminho_imagem, ordem)
                            VALUES (?, ?, ?)
                        ''', (produto_id, image_path, i))
        
        execute_db('INSERT INTO logs_admin (usuario_id, acao, detalhes) VALUES (?, ?, ?)',
                   (session['user_id'], 'criar_produto', f'Produto "{nome}" criado'))
        
        flash('Produto criado com sucesso!', 'success')
        return redirect(url_for('admin.produtos'))
    
    produtos = query_db('''
        SELECT p.*, c.nome as categoria_nome,
               (SELECT caminho_imagem FROM produto_imagens WHERE produto_id = p.id ORDER BY ordem LIMIT 1) as imagem_principal
        FROM produtos p
        JOIN categorias c ON p.categoria_id = c.id
        ORDER BY p.criado_em DESC
    ''')
    
    categorias = query_db('SELECT * FROM categorias WHERE ativo = 1 ORDER BY nome')
    
    return render_template('admin/produtos.html', produtos=produtos, categorias=categorias)

@admin_bp.route('/produtos/<int:id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_produto(id):
    produto = query_db('SELECT * FROM produtos WHERE id = ?', [id], one=True)
    
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('admin.produtos'))
    
    if request.method == 'POST':
        categoria_id = request.form.get('categoria_id')
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        peso = request.form.get('peso') or None
        dimensoes = request.form.get('dimensoes') or None
        marca = request.form.get('marca') or None
        
        try:
            preco = float(request.form.get('preco'))
            if preco < 0:
                raise ValueError("Preço não pode ser negativo")
        except (ValueError, TypeError):
            flash('Preço inválido. Insira um número válido.', 'danger')
            categorias = query_db('SELECT * FROM categorias WHERE ativo = 1 ORDER BY nome')
            imagens = query_db('SELECT * FROM produto_imagens WHERE produto_id = ? ORDER BY ordem', [id])
            return render_template('admin/editar_produto.html', produto=produto, categorias=categorias, imagens=imagens)
        
        try:
            quantidade_estoque = int(request.form.get('quantidade_estoque'))
            if quantidade_estoque < 0:
                raise ValueError("Quantidade não pode ser negativa")
        except (ValueError, TypeError):
            flash('Quantidade em estoque inválida. Insira um número inteiro válido.', 'danger')
            categorias = query_db('SELECT * FROM categorias WHERE ativo = 1 ORDER BY nome')
            imagens = query_db('SELECT * FROM produto_imagens WHERE produto_id = ? ORDER BY ordem', [id])
            return render_template('admin/editar_produto.html', produto=produto, categorias=categorias, imagens=imagens)
        
        execute_db('''
            UPDATE produtos 
            SET categoria_id = ?, nome = ?, descricao = ?, preco = ?, quantidade_estoque = ?,
                peso = ?, dimensoes = ?, marca = ?, atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (categoria_id, nome, descricao, preco, quantidade_estoque, peso, dimensoes, marca, id))
        
        execute_db('INSERT INTO logs_admin (usuario_id, acao, detalhes) VALUES (?, ?, ?)',
                   (session['user_id'], 'editar_produto', f'Produto ID {id} editado'))
        
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin.produtos'))
    
    categorias = query_db('SELECT * FROM categorias WHERE ativo = 1 ORDER BY nome')
    imagens = query_db('SELECT * FROM produto_imagens WHERE produto_id = ? ORDER BY ordem', [id])
    
    return render_template('admin/editar_produto.html', produto=produto, categorias=categorias, imagens=imagens)

@admin_bp.route('/produtos/<int:id>/toggle-status', methods=['POST'])
@admin_required
def toggle_produto_status(id):
    produto = query_db('SELECT ativo, nome FROM produtos WHERE id = ?', [id], one=True)
    novo_status = 0 if produto['ativo'] else 1
    
    execute_db('UPDATE produtos SET ativo = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?', 
               (novo_status, id))
    
    status_text = 'ativado' if novo_status else 'desativado'
    execute_db('INSERT INTO logs_admin (usuario_id, acao, detalhes) VALUES (?, ?, ?)',
                (session['user_id'], 'toggle_produto', f'Produto "{produto["nome"]}" {status_text}'))
    
    flash(f'Produto {status_text} com sucesso!', 'success')
    return redirect(url_for('admin.produtos'))

@admin_bp.route('/pedidos')
@admin_required
def pedidos():
    pedidos = query_db('''
        SELECT p.*, u.nome as cliente_nome, u.email as cliente_email,
               COUNT(pi.id) as total_itens
        FROM pedidos p
        JOIN usuarios u ON p.usuario_id = u.id
        LEFT JOIN pedido_itens pi ON p.id = pi.pedido_id
        GROUP BY p.id
        ORDER BY p.criado_em DESC
    ''')
    
    return render_template('admin/pedidos.html', pedidos=pedidos)

@admin_bp.route('/pedidos/<int:id>')
@admin_required
def pedido_detalhes(id):
    pedido = query_db('''
        SELECT p.*, u.nome as cliente_nome, u.email as cliente_email, u.telefone as cliente_telefone
        FROM pedidos p
        JOIN usuarios u ON p.usuario_id = u.id
        WHERE p.id = ?
    ''', [id], one=True)
    
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('admin.pedidos'))
    
    itens = query_db('''
        SELECT pi.*, pr.nome as produto_nome, pr.sku
        FROM pedido_itens pi
        JOIN produtos pr ON pi.produto_id = pr.id
        WHERE pi.pedido_id = ?
    ''', [id])
    
    return render_template('admin/pedido_detalhes.html', pedido=pedido, itens=itens)

@admin_bp.route('/pedidos/<int:id>/atualizar-status', methods=['POST'])
@admin_required
def atualizar_status_pedido(id):
    novo_status = request.form.get('status')
    
    execute_db('UPDATE pedidos SET status = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?', 
               (novo_status, id))
    
    execute_db('INSERT INTO logs_admin (usuario_id, acao, detalhes) VALUES (?, ?, ?)',
               (session['user_id'], 'atualizar_pedido', f'Status do pedido ID {id} alterado para {novo_status}'))
    
    flash('Status do pedido atualizado com sucesso!', 'success')
    return redirect(url_for('admin.pedido_detalhes', id=id))

@admin_bp.route('/pedidos/<int:id>/confirmar-pagamento', methods=['POST'])
@admin_required
def confirmar_pagamento(id):
    pedido = query_db('SELECT * FROM pedidos WHERE id = ?', [id], one=True)
    
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('admin.pedidos'))
    
    if pedido['metodo_pagamento'] != 'dinheiro':
        flash('Apenas pagamentos em dinheiro podem ser confirmados manualmente.', 'warning')
        return redirect(url_for('admin.pedido_detalhes', id=id))
    
    execute_db('''
        UPDATE pedidos 
        SET confirmado_admin = 1, 
            data_confirmacao_admin = CURRENT_TIMESTAMP, 
            status = 'pago',
            atualizado_em = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (id,))
    
    execute_db('INSERT INTO logs_admin (usuario_id, acao, detalhes) VALUES (?, ?, ?)',
               (session['user_id'], 'confirmar_pagamento_dinheiro', f'Pagamento em dinheiro confirmado para pedido ID {id}'))
    
    flash('Pagamento em dinheiro confirmado com sucesso!', 'success')
    return redirect(url_for('admin.pedido_detalhes', id=id))

@admin_bp.route('/faturamento')
@admin_required
def faturamento():
    periodo = request.args.get('periodo', 'mensal')
    
    if periodo == 'diario':
        data_inicio = datetime.now().date()
    elif periodo == 'semanal':
        data_inicio = datetime.now().date() - timedelta(days=7)
    else:
        data_inicio = datetime.now().date() - timedelta(days=30)
    
    total_vendido = query_db('''
        SELECT COALESCE(SUM(total), 0) as total 
        FROM pedidos 
        WHERE status != "cancelado" AND DATE(criado_em) >= ?
    ''', [data_inicio], one=True)['total']
    
    config = query_db('SELECT comissao_percentual FROM configuracoes_loja WHERE id = 1', one=True)
    comissao_percentual = float(config['comissao_percentual']) if config and config['comissao_percentual'] else 10.0
    comissao_valor = total_vendido * (comissao_percentual / 100)
    lucro_liquido = total_vendido - comissao_valor
    
    vendas_por_categoria = query_db('''
        SELECT c.nome, SUM(pi.subtotal) as total
        FROM pedido_itens pi
        JOIN produtos p ON pi.produto_id = p.id
        JOIN categorias c ON p.categoria_id = c.id
        JOIN pedidos ped ON pi.pedido_id = ped.id
        WHERE ped.status != "cancelado" AND DATE(ped.criado_em) >= ?
        GROUP BY c.id
        ORDER BY total DESC
    ''', [data_inicio])
    
    return render_template('admin/faturamento.html',
                         periodo=periodo,
                         total_vendido=total_vendido,
                         comissao_percentual=comissao_percentual,
                         comissao_valor=comissao_valor,
                         lucro_liquido=lucro_liquido,
                         vendas_por_categoria=vendas_por_categoria)

@admin_bp.route('/faturamento/exportar-csv')
@admin_required
def exportar_csv():
    periodo = request.args.get('periodo', 'mensal')
    
    if periodo == 'diario':
        data_inicio = datetime.now().date()
    elif periodo == 'semanal':
        data_inicio = datetime.now().date() - timedelta(days=7)
    else:
        data_inicio = datetime.now().date() - timedelta(days=30)
    
    pedidos = query_db('''
        SELECT p.id, p.criado_em, u.nome as cliente, p.total, p.status, p.metodo_pagamento
        FROM pedidos p
        JOIN usuarios u ON p.usuario_id = u.id
        WHERE DATE(p.criado_em) >= ?
        ORDER BY p.criado_em DESC
    ''', [data_inicio])
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Data', 'Cliente', 'Total', 'Status', 'Método Pagamento'])
    
    for pedido in pedidos:
        writer.writerow([
            pedido['id'],
            pedido['criado_em'],
            pedido['cliente'],
            f"R$ {pedido['total']:.2f}",
            pedido['status'],
            pedido['metodo_pagamento']
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=faturamento_{periodo}.csv'
    
    return response

@admin_bp.route('/logs')
@admin_required
def logs():
    logs = query_db('''
        SELECT l.*, u.nome as admin_nome
        FROM logs_admin l
        JOIN usuarios u ON l.usuario_id = u.id
        ORDER BY l.criado_em DESC
        LIMIT 100
    ''')
    
    return render_template('admin/logs.html', logs=logs)

@admin_bp.route('/configuracoes', methods=['GET', 'POST'])
@admin_required
def configuracoes():
    if request.method == 'POST':
        nome_loja = request.form.get('nome_loja')
        descricao_loja = request.form.get('descricao_loja')
        email_contato = request.form.get('email_contato')
        telefone_contato = request.form.get('telefone_contato')
        endereco = request.form.get('endereco')
        local_retirada = request.form.get('local_retirada')
        email_notificacao = request.form.get('email_notificacao')
        comissao_percentual = request.form.get('comissao_percentual', '10.0')
        mercadopago_access_token = request.form.get('mercadopago_access_token', '').strip()
        mercadopago_public_key = request.form.get('mercadopago_public_key', '').strip()
        mercadopago_webhook_secret = request.form.get('mercadopago_webhook_secret', '').strip()
        
        try:
            comissao_percentual = float(comissao_percentual)
            if comissao_percentual < 0 or comissao_percentual > 100:
                flash('A comissão deve estar entre 0% e 100%.', 'danger')
                return redirect(url_for('admin.configuracoes'))
        except ValueError:
            flash('Valor de comissão inválido.', 'danger')
            return redirect(url_for('admin.configuracoes'))
        
        logo_path = None
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename:
                logo_path = save_image(logo_file, 'logos', max_size=(500, 500))
                if not logo_path:
                    flash('Erro ao fazer upload da logo. Verifique o formato do arquivo.', 'danger')
                    return redirect(url_for('admin.configuracoes'))
        
        config_exists = query_db('SELECT id, logo_path FROM configuracoes_loja WHERE id = 1', one=True)
        
        if config_exists:
            if logo_path:
                execute_db('''
                    UPDATE configuracoes_loja 
                    SET nome_loja = ?, descricao_loja = ?, email_contato = ?, 
                        telefone_contato = ?, endereco = ?, local_retirada = ?, 
                        email_notificacao = ?, comissao_percentual = ?, 
                        mercadopago_access_token = ?, mercadopago_public_key = ?,
                        mercadopago_webhook_secret = ?, logo_path = ?,
                        atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = 1
                ''', (nome_loja, descricao_loja, email_contato, telefone_contato, endereco, local_retirada, 
                      email_notificacao, comissao_percentual, mercadopago_access_token, mercadopago_public_key, 
                      mercadopago_webhook_secret, logo_path))
            else:
                execute_db('''
                    UPDATE configuracoes_loja 
                    SET nome_loja = ?, descricao_loja = ?, email_contato = ?, 
                        telefone_contato = ?, endereco = ?, local_retirada = ?, 
                        email_notificacao = ?, comissao_percentual = ?, 
                        mercadopago_access_token = ?, mercadopago_public_key = ?,
                        mercadopago_webhook_secret = ?,
                        atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = 1
                ''', (nome_loja, descricao_loja, email_contato, telefone_contato, endereco, local_retirada, 
                      email_notificacao, comissao_percentual, mercadopago_access_token, mercadopago_public_key, mercadopago_webhook_secret))
        else:
            execute_db('''
                INSERT INTO configuracoes_loja (nome_loja, descricao_loja, email_contato, telefone_contato, 
                                                endereco, local_retirada, email_notificacao, comissao_percentual,
                                                mercadopago_access_token, mercadopago_public_key, mercadopago_webhook_secret,
                                                logo_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nome_loja, descricao_loja, email_contato, telefone_contato, endereco, local_retirada, 
                  email_notificacao, comissao_percentual, mercadopago_access_token, mercadopago_public_key, 
                  mercadopago_webhook_secret, logo_path))
        
        execute_db('INSERT INTO logs_admin (usuario_id, acao, detalhes) VALUES (?, ?, ?)',
                   (session['user_id'], 'atualizar_configuracoes', 'Configurações da loja atualizadas'))
        
        flash('Configurações atualizadas com sucesso!', 'success')
        return redirect(url_for('admin.configuracoes'))
    
    config = query_db('SELECT * FROM configuracoes_loja WHERE id = 1', one=True)
    if not config:
        config = {
            'nome_loja': 'E-Shop',
            'descricao_loja': 'Sua loja online de perfumes, roupas e acessórios.',
            'email_contato': 'contato@eshop.com',
            'telefone_contato': '(00) 0000-0000',
            'endereco': '',
            'local_retirada': '',
            'email_notificacao': '',
            'comissao_percentual': 10.0,
            'mercadopago_access_token': '',
            'mercadopago_public_key': '',
            'mercadopago_webhook_secret': ''
        }
    return render_template('admin/configuracoes.html', config=config)

@admin_bp.route('/resetar-produtos-categorias', methods=['POST'])
@admin_required
def resetar_produtos_categorias():
    db = get_db()
    try:
        produtos_em_pedidos = query_db('''
            SELECT DISTINCT produto_id 
            FROM pedido_itens
        ''')
        produtos_em_pedidos_ids = [p['produto_id'] for p in produtos_em_pedidos] if produtos_em_pedidos else []
        
        if produtos_em_pedidos_ids:
            placeholders = ','.join(['?' for _ in produtos_em_pedidos_ids])
            db.execute(f'UPDATE produtos SET ativo = 0 WHERE id IN ({placeholders})', produtos_em_pedidos_ids)
            
            db.execute(f'DELETE FROM produto_imagens WHERE produto_id NOT IN ({placeholders})', produtos_em_pedidos_ids)
            db.execute(f'DELETE FROM produto_atributos WHERE produto_id NOT IN ({placeholders})', produtos_em_pedidos_ids)
            db.execute(f'DELETE FROM produtos WHERE id NOT IN ({placeholders})', produtos_em_pedidos_ids)
        else:
            db.execute('DELETE FROM produto_imagens')
            db.execute('DELETE FROM produto_atributos')
            db.execute('DELETE FROM produtos')
        
        db.execute('UPDATE categorias SET ativo = 0')
        
        db.execute('INSERT INTO logs_admin (usuario_id, acao, detalhes) VALUES (?, ?, ?)',
                   (session['user_id'], 'resetar_database', 'Produtos e categorias foram desativados/removidos do banco de dados'))
        
        db.commit()
        
        produtos_preservados = len(produtos_em_pedidos_ids) if produtos_em_pedidos_ids else 0
        if produtos_preservados > 0:
            flash(f'Reset concluído! {produtos_preservados} produto(s) usado(s) em pedidos foram desativados (preservando histórico). Demais produtos e todas as categorias foram desativados.', 'success')
        else:
            flash('Reset concluído! Todos os produtos e categorias foram removidos. Não havia produtos em pedidos anteriores.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Erro ao resetar banco de dados: {str(e)}', 'danger')
    
    return redirect(url_for('admin.configuracoes'))

@admin_bp.route('/check-new-orders')
@admin_required
def check_new_orders():
    pending_count = query_db('SELECT COUNT(*) as count FROM pedidos WHERE status = ?', ['pendente'], one=True)['count']
    
    latest_order = query_db('''
        SELECT p.id, p.total, u.nome as cliente_nome
        FROM pedidos p
        JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.criado_em DESC
        LIMIT 1
    ''', one=True)
    
    if latest_order:
        return jsonify({
            'has_new_orders': pending_count > 0,
            'pending_count': pending_count,
            'latest_order_id': latest_order['id'],
            'customer_name': latest_order['cliente_nome'],
            'total': float(latest_order['total'])
        })
    
    return jsonify({
        'has_new_orders': False,
        'pending_count': 0,
        'latest_order_id': 0,
        'customer_name': '',
        'total': 0.0
    })
