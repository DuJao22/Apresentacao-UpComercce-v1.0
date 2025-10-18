from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.db import query_db, execute_db
from app.utils.helpers import save_image, validate_cpf
from app.utils.decorators import login_required
import secrets
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

password_reset_tokens = {}

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        if not email or not senha:
            flash('Por favor, preencha email e senha.', 'danger')
            return render_template('auth/login.html')
        
        user = query_db('SELECT * FROM usuarios WHERE email = ? AND ativo = 1', [email], one=True)
        
        if user and check_password_hash(user['senha_hash'], senha):
            session['user_id'] = user['id']
            session['user_name'] = user['nome']
            session['user_role'] = user['perfil']
            session['user_photo'] = user['foto_perfil']
            session.permanent = True
            
            flash(f'Bem-vindo(a), {user["nome"]}!', 'success')
            
            if user['perfil'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('customer.dashboard'))
        else:
            flash('Email ou senha incorretos.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        data_nascimento = request.form.get('data_nascimento')
        telefone = request.form.get('telefone')
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        if not all([nome, cpf, data_nascimento, telefone, email, senha]):
            flash('Por favor, preencha todos os campos.', 'danger')
            return render_template('auth/register.html')
        
        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return render_template('auth/register.html')
        
        if not validate_cpf(cpf):
            flash('CPF inválido.', 'danger')
            return render_template('auth/register.html')
        
        existing_user = query_db('SELECT id FROM usuarios WHERE email = ? OR cpf = ?', [email, cpf], one=True)
        if existing_user:
            flash('Email ou CPF já cadastrado.', 'danger')
            return render_template('auth/register.html')
        
        senha_hash = generate_password_hash(senha)
        
        execute_db('''
            INSERT INTO usuarios (nome, cpf, data_nascimento, telefone, email, senha_hash, perfil)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nome, cpf, data_nascimento, telefone, email, senha_hash, 'cliente'))
        
        flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('shop.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
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
        
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('auth.profile'))
    
    pedidos = query_db('''
        SELECT p.*, COUNT(pi.id) as total_itens
        FROM pedidos p
        LEFT JOIN pedido_itens pi ON p.id = pi.pedido_id
        WHERE p.usuario_id = ?
        GROUP BY p.id
        ORDER BY p.criado_em DESC
    ''', [session['user_id']])
    
    return render_template('auth/profile.html', user=user, pedidos=pedidos)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        if not all([senha_atual, nova_senha, confirmar_senha]):
            flash('Por favor, preencha todos os campos.', 'danger')
            return render_template('auth/change_password.html')
        
        if len(nova_senha) < 6:
            flash('A nova senha deve ter pelo menos 6 caracteres.', 'danger')
            return render_template('auth/change_password.html')
        
        user = query_db('SELECT senha_hash FROM usuarios WHERE id = ?', [session['user_id']], one=True)
        
        if not user:
            flash('Usuário não encontrado.', 'danger')
            return redirect(url_for('auth.logout'))
        
        if not check_password_hash(user['senha_hash'], senha_atual):
            flash('Senha atual incorreta.', 'danger')
            return render_template('auth/change_password.html')
        
        if nova_senha != confirmar_senha:
            flash('As senhas não coincidem.', 'danger')
            return render_template('auth/change_password.html')
        
        nova_senha_hash = generate_password_hash(nova_senha)
        execute_db('UPDATE usuarios SET senha_hash = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?', 
                   (nova_senha_hash, session['user_id']))
        
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        user = query_db('SELECT id, nome FROM usuarios WHERE email = ? AND ativo = 1', [email], one=True)
        
        if user:
            token = secrets.token_urlsafe(32)
            password_reset_tokens[token] = {
                'user_id': user['id'],
                'email': email,
                'expires': datetime.now() + timedelta(hours=1)
            }
            
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            flash(f'Link de recuperação gerado (simulação local): {reset_link}', 'info')
        else:
            flash('Se o email existir, você receberá um link de recuperação.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if token not in password_reset_tokens:
        flash('Token inválido ou expirado.', 'danger')
        return redirect(url_for('auth.login'))
    
    token_data = password_reset_tokens[token]
    
    if datetime.now() > token_data['expires']:
        del password_reset_tokens[token]
        flash('Token expirado. Solicite um novo link de recuperação.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        if nova_senha != confirmar_senha:
            flash('As senhas não coincidem.', 'danger')
            return render_template('auth/reset_password.html')
        
        nova_senha_hash = generate_password_hash(nova_senha)
        execute_db('UPDATE usuarios SET senha_hash = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?',
                   (nova_senha_hash, token_data['user_id']))
        
        del password_reset_tokens[token]
        
        flash('Senha redefinida com sucesso! Faça login com sua nova senha.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html')
