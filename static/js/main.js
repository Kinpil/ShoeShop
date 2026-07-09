// === ГЛОБАЛЬНЫЕ СКРИПТЫ ===

// Обновление количества товаров в корзине
function updateCartCount() {
    fetch('/cart/count/')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('cart-count');
            if (badge) {
                badge.textContent = data.count;
                if (data.count > 0) {
                    badge.style.display = 'inline';
                } else {
                    badge.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Ошибка обновления корзины:', error));
}

// Общение между вкладками (редактирование)
function setupBroadcastChannel() {
    let channel = null;
    try {
        channel = new BroadcastChannel('edit_channel');
    } catch (e) {}
    
    if (channel) {
        channel.onmessage = function(event) {
            if (event.data.type === 'edit_closed') {
                const closedProductId = event.data.productId;
                const currentEditId = localStorage.getItem('editing_product_id');
                if (currentEditId === closedProductId) {
                    localStorage.removeItem('editing_product_id');
                    location.reload();
                }
            }
        };
    }
    return channel;
}

// Автоматическое скрытие уведомлений через 4 секунды
function setupAutoHideAlerts() {
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        });
    }, 4000);
}

// Запуск при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    updateCartCount();
    setupBroadcastChannel();
    setupAutoHideAlerts();
});