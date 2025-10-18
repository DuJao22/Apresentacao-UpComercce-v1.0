# 🛍️ Sistema de E-commerce - Perfumes, Roupas e Acessórios

**Desenvolvido por: João Layon**

Sistema completo de e-commerce para venda de perfumes, roupas e acessórios com painel administrativo avançado, controle de estoque e sistema de faturamento.

## 🚀 Funcionalidades

### Autenticação e Usuários
- ✅ Cadastro de clientes com CPF, data de nascimento, telefone e email
- ✅ Login seguro com hash de senhas (Werkzeug)
- ✅ Upload de foto de perfil para usuários e administradores
- ✅ Recuperação de senha (admin pode resetar qualquer senha)
- ✅ Perfis com permissões: `admin` e `cliente`

### Catálogo de Produtos
- ✅ Categorias personalizadas (Perfumes, Roupas, Acessórios)
- ✅ Produtos com: nome, descrição, preço, SKU, estoque, peso, dimensões, marca
- ✅ Até 5 imagens por produto
- ✅ Atributos opcionais (cor, tamanho) com variações de estoque

### Carrinho e Checkout
- ✅ Carrinho persistente na sessão do usuário
- ✅ Checkout com pagamento simulado
- ✅ Geração automática de pedidos

### Controle de Estoque e Faturamento
- ✅ Controle automático de estoque ao confirmar pedidos
- ✅ Painel de faturamento com total vendido, lucro bruto e comissões
- ✅ Relatórios por período (diário, semanal, mensal)
- ✅ Exportação de relatórios em CSV

### Administração
- ✅ Painel administrativo responsivo
- ✅ Gestão de usuários, produtos, categorias, pedidos e estoque
- ✅ Reset de senha de qualquer usuário
- ✅ Logs de atividade administrativa

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python + Flask
- **Banco de Dados**: SQLite3 (sem ORM)
- **Frontend**: HTML5 + Tailwind CSS
- **Segurança**: Werkzeug (hashing), Flask-WTF (CSRF)
- **Upload de Imagens**: Pillow

## 📦 Instalação e Execução

### No Replit (Recomendado)

1. Clone este repositório no Replit
2. Execute o script de inicialização do banco de dados:
```bash
python init_db.py
```

3. Inicie a aplicação:
```bash
python main.py
```

4. Acesse: `http://localhost:5000`

### Localmente

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd ecommerce
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Inicialize o banco de dados:
```bash
python init_db.py
```

4. Execute a aplicação:
```bash
python main.py
```

5. Acesse: `http://localhost:5000`

## 👤 Credenciais Padrão

**Administrador:**
- Email: `admin@ecommerce.com`
- Senha: `admin123`

⚠️ **Importante**: Altere a senha padrão após o primeiro login!

## 📁 Estrutura do Projeto

```
ecommerce/
├── app/
│   ├── blueprints/          # Módulos Flask (auth, shop, admin, cart)
│   ├── models/              # Modelos de dados
│   ├── templates/           # Templates Jinja2
│   │   ├── layouts/         # Layouts base
│   │   ├── auth/           # Páginas de autenticação
│   │   ├── shop/           # Páginas da loja
│   │   └── admin/          # Painel administrativo
│   ├── static/             # Arquivos estáticos
│   │   ├── css/           # Estilos
│   │   ├── js/            # JavaScript
│   │   └── uploads/       # Imagens de produtos e perfis
│   └── utils/             # Funções auxiliares
├── main.py                # Aplicação principal
├── config.py             # Configurações
├── init_db.py           # Script de inicialização do banco
└── requirements.txt     # Dependências Python
```

## 🎨 Interface

- Design responsivo com Tailwind CSS
- Compatível com dispositivos móveis e desktop
- UX otimizada com fluxo de compra simplificado
- Feedbacks visuais claros em todas as ações

## 🔒 Segurança

- ✅ Hashing de senhas com Werkzeug
- ✅ Proteção CSRF com Flask-WTF
- ✅ Validação de inputs (servidor e cliente)
- ✅ Upload seguro de imagens com validação de tipo
- ✅ Sanitização de dados do banco

## 📊 Recursos Extras

- Sistema de cupons e descontos
- Filtros de busca por categoria, preço e marca
- Página de recomendações de produtos
- Histórico de pedidos no perfil do usuário
- Redimensionamento automático de imagens
- Interface em português (pt-BR)

## 🚀 Deploy no Replit

1. Configure a variável de ambiente `SESSION_SECRET` nas configurações do Replit
2. Use o botão "Run" para iniciar a aplicação
3. A aplicação estará disponível na URL fornecida pelo Replit

## 📝 Licença

Projeto desenvolvido por **João Layon** - Todos os direitos reservados.

## 🤝 Contribuições

Este é um projeto educacional. Para melhorias ou sugestões, entre em contato.

---

**Créditos**: Sistema desenvolvido por João Layon com Flask, SQLite e Tailwind CSS.
