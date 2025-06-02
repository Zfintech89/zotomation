// Global modal system for the application
class ModalSystem {
    constructor() {
        this.modalContainer = null;
        this.setupModalContainer();
    }

    setupModalContainer() {
        // Create modal container if it doesn't exist
        if (!this.modalContainer) {
            this.modalContainer = document.createElement('div');
            this.modalContainer.id = 'modal-system';
            document.body.appendChild(this.modalContainer);
        }
    }

    show({ title, message, type = 'info', buttons = [] }) {
        const modalId = 'modal-' + Date.now();
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = modalId;

        let buttonHtml = '';
        buttons.forEach(button => {
            const btnClass = button.type === 'danger' ? 'btn-danger' : 
                           button.type === 'primary' ? 'btn-primary' : 'btn-secondary';
            buttonHtml += `
                <button class="btn ${btnClass}" data-action="${button.action}">${button.text}</button>
            `;
        });

        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${title}</h2>
                    <button class="close-modal" data-action="close">&times;</button>
                </div>
                <div class="modal-body">
                    ${type === 'warning' ? '<div class="warning-icon"><i class="fas fa-exclamation-triangle"></i></div>' : ''}
                    <p>${message}</p>
                </div>
                <div class="modal-actions">
                    ${buttonHtml}
                </div>
            </div>
        `;

        this.modalContainer.appendChild(modal);
        
        // Add animation class after a brief delay to trigger the animation
        setTimeout(() => modal.classList.add('show'), 10);

        return new Promise((resolve) => {
            modal.addEventListener('click', (e) => {
                const action = e.target.closest('[data-action]')?.dataset.action;
                if (action) {
                    if (action === 'close') {
                        this.hide(modalId);
                        resolve(false);
                    } else {
                        this.hide(modalId);
                        resolve(action);
                    }
                }
            });
        });
    }

    hide(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.remove();
            }, 300); // Match the CSS transition duration
        }
    }

    confirm(message, { title = 'Confirm', okText = 'OK', cancelText = 'Cancel' } = {}) {
        return this.show({
            title,
            message,
            type: 'warning',
            buttons: [
                { text: cancelText, action: 'cancel', type: 'secondary' },
                { text: okText, action: 'confirm', type: 'primary' }
            ]
        }).then(result => result === 'confirm');
    }

    alert(message, { title = 'Alert', okText = 'OK' } = {}) {
        return this.show({
            title,
            message,
            type: 'info',
            buttons: [
                { text: okText, action: 'ok', type: 'primary' }
            ]
        });
    }
}

// Initialize global modal system
window.modalSystem = new ModalSystem();
