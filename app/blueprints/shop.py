from flask import Blueprint, render_template, request
from app.utils.db import query_db

shop_bp = Blueprint('shop', __name__)

@shop_bp.route('/')
def index():
    categorias = query_db('SELECT * FROM categorias WHERE ativo = 1 ORDER BY nome')
    
    produtos_destaque = query_db('''
        SELECT p.*, c.nome as categoria_nome, 
               (SELECT caminho_imagem FROM produto_imagens WHERE produto_id = p.id ORDER BY ordem LIMIT 1) as imagem_principal
        FROM produtos p
        JOIN categorias c ON p.categoria_id = c.id
        WHERE p.ativo = 1 AND p.quantidade_estoque > 0
        ORDER BY p.criado_em DESC
        LIMIT 12
    ''')
    
    return render_template('shop/index.html', categorias=categorias, produtos=produtos_destaque)

@shop_bp.route('/categoria/<slug>')
def categoria(slug):
    categoria = query_db('SELECT * FROM categorias WHERE slug = ? AND ativo = 1', [slug], one=True)
    if not categoria:
        return "Categoria não encontrada", 404
    
    produtos = query_db('''
        SELECT p.*, 
               (SELECT caminho_imagem FROM produto_imagens WHERE produto_id = p.id ORDER BY ordem LIMIT 1) as imagem_principal
        FROM produtos p
        WHERE p.categoria_id = ? AND p.ativo = 1
        ORDER BY p.nome
    ''', [categoria['id']])
    
    return render_template('shop/categoria.html', categoria=categoria, produtos=produtos)

@shop_bp.route('/produto/<int:id>')
def produto(id):
    produto = query_db('''
        SELECT p.*, c.nome as categoria_nome, c.slug as categoria_slug
        FROM produtos p
        JOIN categorias c ON p.categoria_id = c.id
        WHERE p.id = ? AND p.ativo = 1
    ''', [id], one=True)
    
    if not produto:
        return "Produto não encontrado", 404
    
    imagens = query_db('SELECT * FROM produto_imagens WHERE produto_id = ? ORDER BY ordem', [id])
    atributos = query_db('SELECT * FROM produto_atributos WHERE produto_id = ?', [id])
    
    produtos_relacionados = query_db('''
        SELECT p.*, 
               (SELECT caminho_imagem FROM produto_imagens WHERE produto_id = p.id ORDER BY ordem LIMIT 1) as imagem_principal
        FROM produtos p
        WHERE p.categoria_id = ? AND p.id != ? AND p.ativo = 1
        ORDER BY RANDOM()
        LIMIT 4
    ''', [produto['categoria_id'], id])
    
    return render_template('shop/produto.html', produto=produto, imagens=imagens, 
                         atributos=atributos, produtos_relacionados=produtos_relacionados)

@shop_bp.route('/busca')
def busca():
    query = request.args.get('q', '')
    categoria_id = request.args.get('categoria', '')
    
    sql = '''
        SELECT p.*, c.nome as categoria_nome,
               (SELECT caminho_imagem FROM produto_imagens WHERE produto_id = p.id ORDER BY ordem LIMIT 1) as imagem_principal
        FROM produtos p
        JOIN categorias c ON p.categoria_id = c.id
        WHERE p.ativo = 1
    '''
    params = []
    
    if query:
        sql += ' AND (p.nome LIKE ? OR p.descricao LIKE ? OR p.marca LIKE ?)'
        params.extend([f'%{query}%', f'%{query}%', f'%{query}%'])
    
    if categoria_id:
        sql += ' AND p.categoria_id = ?'
        params.append(categoria_id)
    
    sql += ' ORDER BY p.nome'
    
    produtos = query_db(sql, params)
    categorias = query_db('SELECT * FROM categorias WHERE ativo = 1 ORDER BY nome')
    
    return render_template('shop/busca.html', produtos=produtos, categorias=categorias, 
                         query=query, categoria_id=categoria_id)
