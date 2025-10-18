import os
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app
import secrets
from config import Config

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_image(file, folder, max_size=(800, 800)):
    if not file or not file.filename:
        return None
        
    if not allowed_file(file.filename):
        return None
        
    try:
        filename = secure_filename(file.filename)
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(filename)
        new_filename = random_hex + f_ext
        
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_path, exist_ok=True)
        
        file_path = os.path.join(upload_path, new_filename)
        
        img = Image.open(file)
        img.thumbnail(max_size)
        img.save(file_path, quality=85, optimize=True)
        
        return os.path.join('uploads', folder, new_filename)
    except (IOError, OSError) as e:
        print(f"Erro ao salvar imagem: {e}")
        return None

def format_currency(value):
    return f"R$ {value:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')

def format_cpf(cpf):
    cpf = ''.join(filter(str.isdigit, cpf))
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

def validate_cpf(cpf):
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False
    
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10 % 11) % 10
    
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10 % 11) % 10
    
    return cpf[-2:] == f"{digito1}{digito2}"
