import sqlite3
import os

DATABASE = 'ecommerce.db'

def migrate_mercadopago():
    """Adiciona campos necessários para integração com Mercado Pago"""
    
    if not os.path.exists(DATABASE):
        print(f"❌ Banco de dados não encontrado: {DATABASE}")
        print("Execute init_db.py primeiro para criar o banco de dados.")
        return
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        print("🔄 Iniciando migração para Mercado Pago...")
        
        cursor.execute("PRAGMA table_info(configuracoes_loja)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'mercadopago_access_token' not in columns:
            cursor.execute('''
                ALTER TABLE configuracoes_loja 
                ADD COLUMN mercadopago_access_token TEXT
            ''')
            print("✓ Campo mercadopago_access_token adicionado")
        
        if 'mercadopago_public_key' not in columns:
            cursor.execute('''
                ALTER TABLE configuracoes_loja 
                ADD COLUMN mercadopago_public_key TEXT
            ''')
            print("✓ Campo mercadopago_public_key adicionado")
        
        if 'mercadopago_webhook_secret' not in columns:
            cursor.execute('''
                ALTER TABLE configuracoes_loja 
                ADD COLUMN mercadopago_webhook_secret TEXT
            ''')
            print("✓ Campo mercadopago_webhook_secret adicionado")
        
        cursor.execute("PRAGMA table_info(pedidos)")
        pedidos_columns = [row[1] for row in cursor.fetchall()]
        
        if 'mercadopago_payment_id' not in pedidos_columns:
            cursor.execute('''
                ALTER TABLE pedidos 
                ADD COLUMN mercadopago_payment_id TEXT
            ''')
            print("✓ Campo mercadopago_payment_id adicionado")
        
        if 'mercadopago_preference_id' not in pedidos_columns:
            cursor.execute('''
                ALTER TABLE pedidos 
                ADD COLUMN mercadopago_preference_id TEXT
            ''')
            print("✓ Campo mercadopago_preference_id adicionado")
        
        if 'confirmado_admin' not in pedidos_columns:
            cursor.execute('''
                ALTER TABLE pedidos 
                ADD COLUMN confirmado_admin INTEGER DEFAULT 0
            ''')
            print("✓ Campo confirmado_admin adicionado")
        
        if 'data_confirmacao_admin' not in pedidos_columns:
            cursor.execute('''
                ALTER TABLE pedidos 
                ADD COLUMN data_confirmacao_admin TIMESTAMP
            ''')
            print("✓ Campo data_confirmacao_admin adicionado")
        
        conn.commit()
        print("✅ Migração concluída com sucesso!")
        
    except sqlite3.Error as e:
        print(f"❌ Erro durante a migração: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_mercadopago()
