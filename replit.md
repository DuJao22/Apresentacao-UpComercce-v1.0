# Sistema de E-commerce - João Layon

## Overview
This is a complete e-commerce system developed with Python Flask, designed for selling perfumes, clothing, and accessories. It features a comprehensive administrative panel, inventory control, invoicing system, and a responsive user interface. The project aims to provide a robust and scalable platform for online retail, focusing on ease of management and a rich user experience.

## User Preferences
- I prefer simple language.
- I like functional programming.
- I want iterative development.
- Ask before making major changes.
- I prefer detailed explanations.
- Do not make changes to the folder `Z`.
- Do not make changes to the file `Y`.

## System Architecture

### UI/UX Decisions
The system utilizes HTML5 and Tailwind CSS for a modern, responsive interface, ensuring compatibility across mobile and desktop devices. Font Awesome is used for iconography. The administrative panel and customer area are designed with intuitive navigation and visual feedback. A custom logo upload feature allows for extensive branding, affecting headers, footers, favicons, and notifications.

### Technical Implementations
- **Backend**: Python 3.11 with Flask.
- **Database**: SQLite3, managed without an ORM for direct control.
- **Security**: Werkzeug for password hashing and Flask-WTF for CSRF protection.
- **Image Processing**: Pillow for handling product images, including resizing and optimization.
- **Payment Integration**: Mercado Pago SDK for online transactions.

### Feature Specifications
- **Authentication & User Management**: Secure login, user registration (customers and admin), profile management, and password recovery.
- **Product Catalog**: Customizable categories, product details (name, description, price, SKU, stock, weight, dimensions, brand), up to 5 images per product, optional attributes (color, size), search, and filtering. Includes pre-populated example products and professional images.
- **Shopping Cart & Checkout**: Persistent cart, quantity updates, shipping address selection, integration with Mercado Pago for online payments (card, PIX, boleto), and cash payment option with admin confirmation. Webhooks are used for automatic payment confirmation.
- **Inventory Control**: Automatic stock updates upon order confirmation and low stock alerts.
- **Administrative Panel**: Dashboard with metrics, user management, category and product management (create, edit, activate/deactivate), order management (view, update status), invoicing with reports, configurable commission, CSV export, activity logs, and store settings (name, description, contacts, Mercado Pago credentials, logo). Includes real-time notification system for new orders and detailed order statuses.
- **Customer Area**: Professional dashboard, order management with status filters, detailed order view with visual tracking timelines, order cancellation for pending orders, account settings, and password alteration.
- **Responsive Interface**: All interfaces, including admin and customer areas, are optimized for various screen sizes with parity of data presentation.

### System Design Choices
- **Modular Blueprints**: Application logic is organized into Flask blueprints (auth, shop, cart, admin, customer) for maintainability.
- **Database Schema**: Key tables include `usuarios`, `categorias`, `produtos`, `produto_imagens`, `produto_atributos`, `pedidos`, `pedido_itens`, `logs_admin`, and `configuracoes_loja`.
- **Configuration Management**: Store settings are configurable via the admin panel, including the ability to upload a custom logo that dynamically updates across the entire system.
- **Database Migration**: A `migrate_database.py` script is provided for schema updates on existing databases, and `init_db.py` for fresh database creation.

## External Dependencies
- **Mercado Pago SDK**: Integrated for processing online payments (credit card, PIX, boleto).
- **Werkzeug**: Used for secure password hashing.
- **Flask-WTF**: Utilized for CSRF protection in web forms.
- **Pillow**: Employed for image manipulation and processing, primarily for product images and custom logos.
- **Tailwind CSS**: Framework for styling the responsive user interface.
- **Font Awesome**: Provides a library of icons used throughout the application.