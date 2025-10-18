import os
from flask import Flask, session
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    app.config['DATABASE'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ecommerce.db')
    app.config['WTF_CSRF_ENABLED'] = True
    
    csrf = CSRFProtect(app)
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'products'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)
    
    from app.blueprints.auth import auth_bp
    from app.blueprints.shop import shop_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.cart import cart_bp
    from app.blueprints.customer import customer_bp
    from app.blueprints.webhook import webhook_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(webhook_bp)
    
    csrf.exempt(webhook_bp)
    
    from app.utils.db import close_db
    app.teardown_appcontext(close_db)
    
    @app.context_processor
    def inject_cart_count():
        cart = session.get('cart', {})
        cart_count = sum(item['quantity'] for item in cart.values())
        return {'cart_count': cart_count}
    
    @app.context_processor
    def inject_store_config():
        from app.utils.db import query_db
        config = query_db('SELECT * FROM configuracoes_loja WHERE id = 1', one=True)
        if not config:
            config = {
                'nome_loja': 'E-Shop',
                'descricao_loja': 'Sua loja online de perfumes, roupas e acessórios.',
                'email_contato': 'contato@eshop.com',
                'telefone_contato': '(00) 0000-0000',
                'endereco': None,
                'local_retirada': None,
                'email_notificacao': None
            }
        return {'store_config': config}
    
    @app.context_processor
    def inject_admin_notifications():
        from app.utils.db import query_db
        if session.get('user_role') == 'admin':
            pedidos_pendentes = query_db(
                'SELECT COUNT(*) as count FROM pedidos WHERE status = ?', 
                ['pendente'], 
                one=True
            )['count']
            return {'pedidos_pendentes_count': pedidos_pendentes}
        return {'pedidos_pendentes_count': 0}
    
    return app
