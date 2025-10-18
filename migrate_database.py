import sqlite3
import os

DATABASE = 'ecommerce.db'

def migrate_database():
    """Adiciona colunas faltantes no banco de dados existente"""
    
    if not os.path.exists(DATABASE):
        print(f"❌ Erro: Banco de dados não encontrado: {DATABASE}")
        print("Execute 'python init_db.py' primeiro para criar o banco de dados.")
        return
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("🔄 Iniciando migração do banco de dados...")
    
    # Adicionar colunas na tabela configuracoes_loja
    try:
        cursor.execute("ALTER TABLE configuracoes_loja ADD COLUMN local_retirada TEXT")
        print("✓ Coluna 'local_retirada' adicionada à tabela configuracoes_loja")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("• Coluna 'local_retirada' já existe")
        else:
            print(f"❌ Erro ao adicionar 'local_retirada': {e}")
    
    try:
        cursor.execute("ALTER TABLE configuracoes_loja ADD COLUMN email_notificacao TEXT")
        print("✓ Coluna 'email_notificacao' adicionada à tabela configuracoes_loja")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("• Coluna 'email_notificacao' já existe")
        else:
            print(f"❌ Erro ao adicionar 'email_notificacao': {e}")
    
    # Adicionar coluna tipo_entrega na tabela pedidos
    try:
        cursor.execute("ALTER TABLE pedidos ADD COLUMN tipo_entrega TEXT DEFAULT 'entrega'")
        print("✓ Coluna 'tipo_entrega' adicionada à tabela pedidos")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("• Coluna 'tipo_entrega' já existe")
        else:
            print(f"❌ Erro ao adicionar 'tipo_entrega': {e}")
    
    # Adicionar coluna comissao_percentual na tabela configuracoes_loja
    try:
        cursor.execute("ALTER TABLE configuracoes_loja ADD COLUMN comissao_percentual REAL DEFAULT 10.0")
        print("✓ Coluna 'comissao_percentual' adicionada à tabela configuracoes_loja")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("• Coluna 'comissao_percentual' já existe")
        else:
            print(f"❌ Erro ao adicionar 'comissao_percentual': {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Migração concluída com sucesso!")

if __name__ == '__main__':
    migrate_database()
