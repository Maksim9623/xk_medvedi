// Функции для работы с составом
function updateLineup(lineupId, userId) {
    const position = document.getElementById(`position-${userId}`).value;
    const line = document.getElementById(`line-${userId}`).value;
    
    fetch('/update_lineup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'lineup_id': lineupId,
            'user_id': userId,
            'position': position,
            'line': line
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Состав обновлен', 'success');
        } else {
            showNotification('Ошибка обновления', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Ошибка сети', 'error');
    });
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = notification notificption-${type};
    notification.textContent = message;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem;
        border-radius: 4px;
        color: white;
        z-index: 1000;
        ${type === 'success' ? 'background-color: #27ae60;' : 'background-color: #e74c3c;'}
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Обработчики для модальных окон и других интерактивных элементов
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация tooltips
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', showTooltip);
        tooltip.addEventListener('mouseleave', hideTooltip);
    });
});

function showTooltip(e) {
    const tooltipText = this.getAttribute('data-tooltip');
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = tooltipText;
    tooltip.style.cssText = `
        position: absolute;
        background: #333;
        color: white;
        padding: 0.5rem;
        border-radius: 4px;
        font-size: 0.9rem;
        z-index: 1000;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = this.getBoundingClientRect();
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
    tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
    
    this.tooltip = tooltip;
}

function hideTooltip() {
    if (this.tooltip) {
        this.tooltip.remove();
    }
}