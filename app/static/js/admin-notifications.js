// Sistema de Notificações Push para Admin
let lastPedidoId = 0;

// Solicitar permissão para notificações
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                console.log('Permissão de notificação concedida');
                showNotification('Notificações Ativadas', 'Você receberá alertas de novos pedidos!', 'success');
            }
        });
    }
}

// Mostrar notificação do navegador
function showBrowserNotification(title, body) {
    if ('Notification' in window && Notification.permission === 'granted') {
        const logoPath = window.STORE_LOGO_PATH || '/static/favicon.svg';
        const notification = new Notification(title, {
            body: body,
            icon: logoPath,
            badge: logoPath,
            tag: 'novo-pedido',
            requireInteraction: true,
            vibrate: [200, 100, 200]
        });

        notification.onclick = function() {
            window.focus();
            window.location.href = '/admin/pedidos';
            notification.close();
        };

        // Auto-fechar após 10 segundos
        setTimeout(() => notification.close(), 10000);
    }
}

// Mostrar pop-up na tela
function showNotification(title, message, type = 'info') {
    const notification = document.createElement('div');
    const bgColor = {
        'success': 'bg-green-500',
        'info': 'bg-blue-500',
        'warning': 'bg-yellow-500',
        'danger': 'bg-red-500'
    }[type] || 'bg-blue-500';
    
    notification.className = `fixed top-20 right-4 ${bgColor} text-white px-6 py-4 rounded-lg shadow-2xl z-50 max-w-sm animate-slide-in-right`;
    notification.innerHTML = `
        <div class="flex items-center gap-3">
            <i class="fas fa-bell text-2xl"></i>
            <div class="flex-1">
                <h4 class="font-bold">${title}</h4>
                <p class="text-sm">${message}</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="text-white hover:text-gray-200">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remover após 8 segundos
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 8000);
}

// Verificar novos pedidos a cada 10 segundos
async function checkNewOrders() {
    try {
        const response = await fetch('/admin/check-new-orders');
        const data = await response.json();
        
        if (data.has_new_orders && data.latest_order_id > lastPedidoId) {
            lastPedidoId = data.latest_order_id;
            
            // Atualizar badge de notificação
            updateNotificationBadge(data.pending_count);
            
            // Mostrar pop-up na tela
            showNotification(
                '🛍️ Novo Pedido Recebido!',
                `Pedido #${data.latest_order_id} de ${data.customer_name}`,
                'warning'
            );
            
            // Mostrar notificação do navegador
            showBrowserNotification(
                '🛍️ Novo Pedido Recebido!',
                `Pedido #${data.latest_order_id} de ${data.customer_name} - R$ ${data.total.toFixed(2)}`
            );
            
            // Tocar som de notificação
            playNotificationSound();
        }
    } catch (error) {
        console.error('Erro ao verificar pedidos:', error);
    }
}

// Atualizar badge de notificação no menu
function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }
}

// Tocar som de notificação
function playNotificationSound() {
    // Criar um beep simples usando Web Audio API
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
}

// Inicializar quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    // Obter ID do último pedido ao carregar
    fetch('/admin/check-new-orders')
        .then(response => response.json())
        .then(data => {
            lastPedidoId = data.latest_order_id || 0;
            updateNotificationBadge(data.pending_count);
        });
    
    // Verificar novos pedidos a cada 10 segundos
    setInterval(checkNewOrders, 10000);
    
    // Solicitar permissão de notificação após 2 segundos
    setTimeout(requestNotificationPermission, 2000);
});

// Adicionar CSS para animação
const style = document.createElement('style');
style.textContent = `
    @keyframes slide-in-right {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    .animate-slide-in-right {
        animation: slide-in-right 0.3s ease-out;
    }
`;
document.head.appendChild(style);
