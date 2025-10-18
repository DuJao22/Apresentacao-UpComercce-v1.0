import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE = 'ecommerce.db'

def init_database():
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print(f"Banco de dados existente removido: {DATABASE}")
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            data_nascimento DATE NOT NULL,
            telefone TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            perfil TEXT NOT NULL DEFAULT 'cliente',
            foto_perfil TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            descricao TEXT,
            slug TEXT UNIQUE NOT NULL,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco REAL NOT NULL,
            sku TEXT UNIQUE NOT NULL,
            quantidade_estoque INTEGER NOT NULL DEFAULT 0,
            peso REAL,
            dimensoes TEXT,
            marca TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produto_imagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            caminho_imagem TEXT NOT NULL,
            ordem INTEGER DEFAULT 0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos (id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produto_atributos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            valor TEXT NOT NULL,
            estoque_variacao INTEGER DEFAULT 0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos (id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente',
            metodo_pagamento TEXT,
            endereco_entrega TEXT,
            observacoes TEXT,
            tipo_entrega TEXT DEFAULT 'entrega',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedido_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id) ON DELETE CASCADE,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs_admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            acao TEXT NOT NULL,
            detalhes TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracoes_loja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_loja TEXT NOT NULL DEFAULT 'E-Shop',
            descricao_loja TEXT NOT NULL DEFAULT 'Sua loja online de perfumes, roupas e acessórios.',
            email_contato TEXT NOT NULL DEFAULT 'contato@eshop.com',
            telefone_contato TEXT NOT NULL DEFAULT '(00) 0000-0000',
            endereco TEXT,
            local_retirada TEXT,
            email_notificacao TEXT,
            comissao_percentual REAL DEFAULT 10.0,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        INSERT INTO usuarios (nome, cpf, data_nascimento, telefone, email, senha_hash, perfil)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Administrador',
        '000.000.000-00',
        '1990-01-01',
        '(00) 00000-0000',
        'admin@ecommerce.com',
        generate_password_hash('admin123'),
        'admin'
    ))
    
    cursor.execute('''
        INSERT INTO categorias (nome, descricao, slug)
        VALUES 
            ('Perfumes', 'Fragrâncias importadas e nacionais', 'perfumes'),
            ('Roupas', 'Vestuário masculino e feminino', 'roupas'),
            ('Acessórios', 'Acessórios diversos para todos os estilos', 'acessorios')
    ''')
    
    cursor.execute('''
        INSERT INTO configuracoes_loja (nome_loja, descricao_loja, email_contato, telefone_contato)
        VALUES ('E-Shop', 'Sua loja online de perfumes, roupas e acessórios.', 'contato@eshop.com', '(00) 0000-0000')
    ''')
    
    conn.commit()
    conn.close()
    
    print("✓ Banco de dados inicializado com sucesso!")
    print("✓ Usuário administrador criado:")
    print("  Email: admin@ecommerce.com")
    print("  Senha: admin123")
    print("✓ Categorias padrão criadas: Perfumes, Roupas, Acessórios")

if __name__ == '__main__':
    init_database()
