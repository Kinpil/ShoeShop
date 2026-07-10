// === СКРИПТЫ ДЛЯ СТРАНИЦЫ СПИСКА ТОВАРОВ ===

document.addEventListener('DOMContentLoaded', function() {
    // Поиск по Enter
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.form.submit();
            }
        });
    }
    
    // Валидация цены — только положительные числа
    const priceInputs = document.querySelectorAll('#price-min, #price-max');
    priceInputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.value < 0) {
                this.value = 0;
            }
        });
    });
    
    // Сортировка — применяется сразу
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            this.form.submit();
        });
    }
    
    // Проверяем активные фильтры
    function checkActiveFilters() {
        const category = document.getElementById('category-select');
        const supplier = document.getElementById('supplier-select');
        const priceMin = document.getElementById('price-min');
        const priceMax = document.getElementById('price-max');
        
        return (category && category.value) || 
               (supplier && supplier.value) || 
               (priceMin && priceMin.value) || 
               (priceMax && priceMax.value);
    }
    
    // Показываем индикатор активных фильтров
    const filtersToggle = document.getElementById('filtersToggle');
    if (filtersToggle && checkActiveFilters()) {
        filtersToggle.classList.add('border-danger');
    }
});

// === ОБЩЕНИЕ МЕЖДУ ВКЛАДКАМИ (для редактирования) ===
document.addEventListener('DOMContentLoaded', function() {
    // === ОБНОВЛЕНИЕ КНОПОК НА ГЛАВНОЙ СТРАНИЦЕ ===
    function updateEditButtons() {
        const currentEditId = localStorage.getItem('editing_product_id');
        const editButtons = document.querySelectorAll('.edit-btn');
        
        editButtons.forEach(button => {
            const productId = button.dataset.productId;
            const parent = button.parentNode;
            
            // Удаляем старые сообщения
            const oldMessage = parent.querySelector('.editing-message');
            if (oldMessage) oldMessage.remove();
            
            // Показываем кнопку
            button.style.display = 'inline-block';
            
            // Если этот товар редактируется
            if (currentEditId && currentEditId === productId) {
                button.style.display = 'none';
                const message = document.createElement('span');
                message.className = 'badge bg-warning text-dark ms-2 editing-message';
                message.textContent = '⏳ Редактируется';
                parent.appendChild(message);
            }
        });
    }
    
    // === ПРИ КЛИКЕ НА КНОПКУ РЕДАКТИРОВАНИЯ ===
    document.querySelectorAll('.edit-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const productId = this.dataset.productId;
            localStorage.setItem('editing_product_id', productId);
            updateEditButtons();
        });
    });
    
    // === СЛУШАЕМ СООБЩЕНИЯ ОТ ДРУГИХ ВКЛАДОК ===
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
                    updateEditButtons();
                }
            }
        };
    }
    
    // === ПРИ ЗАКРЫТИИ ВКЛАДКИ (редактирование) ===
    window.addEventListener('beforeunload', function() {
        const isEditPage = window.location.pathname.includes('/edit/');
        if (isEditPage) {
            const productId = localStorage.getItem('editing_product_id');
            if (productId && channel) {
                channel.postMessage({
                    type: 'edit_closed',
                    productId: productId
                });
            }
            localStorage.removeItem('editing_product_id');
        }
    });
    
    // === ПРИ ЗАГРУЗКЕ СТРАНИЦЫ ===
    updateEditButtons();
    
    // === ПРИ ПЕРЕКЛЮЧЕНИИ ВКЛАДОК ===
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            updateEditButtons();
        }
    });
});