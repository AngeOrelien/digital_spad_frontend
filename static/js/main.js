// Gestion des messages flash
document.addEventListener('DOMContentLoaded', function () {
    // Auto-fermeture des messages flash
    setTimeout(function () {
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(function (message) {
            message.style.opacity = '0';
            setTimeout(function () {
                message.remove();
            }, 500);
        });
    }, 5000);

    // Bouton de fermeture des messages
    document.querySelectorAll('.flash-close').forEach(function (button) {
        button.addEventListener('click', function () {
            this.parentElement.remove();
        });
    });

    // Menu mobile
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function () {
            mobileMenu.classList.toggle('hidden');
            mobileMenu.classList.toggle('block');
        });
    }

    // Toggle sidebar sur mobile
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('-translate-x-full');
        });
    }

    // Dropdown menus
    document.querySelectorAll('[x-data]').forEach(function (element) {
        // Simple gestion des dropdowns Alpine.js style
        if (element.innerHTML.includes('x-show')) {
            const button = element.querySelector('button');
            const dropdown = element.querySelector('[x-show]');

            if (button && dropdown) {
                button.addEventListener('click', function (e) {
                    e.stopPropagation();
                    const isHidden = dropdown.style.display === 'none';
                    dropdown.style.display = isHidden ? 'block' : 'none';
                });

                // Fermer au clic ailleurs
                document.addEventListener('click', function () {
                    dropdown.style.display = 'none';
                });

                dropdown.addEventListener('click', function (e) {
                    e.stopPropagation();
                });
            }
        }
    });
});

// Gestion de l'authentification
const Auth = {
    // Vérifier si l'utilisateur est connecté
    isAuthenticated: function () {
        return localStorage.getItem('spad_token') !== null;
    },

    // Sauvegarder le token
    saveToken: function (token, userData) {
        localStorage.setItem('spad_token', token);
        localStorage.setItem('spad_user', JSON.stringify(userData));
    },

    // Récupérer le token
    getToken: function () {
        return localStorage.getItem('spad_token');
    },

    // Récupérer les données utilisateur
    getUser: function () {
        const user = localStorage.getItem('spad_user');
        return user ? JSON.parse(user) : null;
    },

    // Déconnexion
    logout: function () {
        localStorage.removeItem('spad_token');
        localStorage.removeItem('spad_user');
        window.location.href = '/login';
    },

    // Vérifier les permissions
    hasRole: function (role) {
        const user = this.getUser();
        return user && user.role === role;
    }
};

// Requêtes API
const API = {
    baseUrl: '/api/proxy',

    // Headers par défaut
    getHeaders: function () {
        const headers = {
            'Content-Type': 'application/json'
        };

        const token = Auth.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    },

    // Requête GET
    get: async function (endpoint) {
        try {
            const response = await fetch(`${this.baseUrl}/${endpoint}`, {
                headers: this.getHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('GET request failed:', error);
            throw error;
        }
    },

    // Requête POST
    post: async function (endpoint, data) {
        try {
            const response = await fetch(`${this.baseUrl}/${endpoint}`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('POST request failed:', error);
            throw error;
        }
    },

    // Requête PUT
    put: async function (endpoint, data) {
        try {
            const response = await fetch(`${this.baseUrl}/${endpoint}`, {
                method: 'PUT',
                headers: this.getHeaders(),
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('PUT request failed:', error);
            throw error;
        }
    },

    // Requête DELETE
    delete: async function (endpoint) {
        try {
            const response = await fetch(`${this.baseUrl}/${endpoint}`, {
                method: 'DELETE',
                headers: this.getHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('DELETE request failed:', error);
            throw error;
        }
    }
};

// Utilitaires
const Utils = {
    // Formater une date
    formatDate: function (dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    },

    // Formater une date avec heure
    formatDateTime: function (dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Afficher une notification
    showNotification: function (message, type = 'info') {
        const colors = {
            'success': 'bg-green-500',
            'error': 'bg-red-500',
            'warning': 'bg-yellow-500',
            'info': 'bg-blue-500'
        };

        const notification = document.createElement('div');
        notification.className = `fixed bottom-4 right-4 text-white px-6 py-3 rounded-lg shadow-lg ${colors[type]} animate-fade-in z-50`;
        notification.innerHTML = `
            ${message}
            <button class="ml-4" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    },

    // Confirmation
    confirm: function (message) {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50';
            modal.innerHTML = `
                <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
                    <div class="p-6">
                        <h3 class="text-lg font-medium text-gray-900 mb-4">Confirmation</h3>
                        <p class="text-gray-600 mb-6">${message}</p>
                        <div class="flex justify-end space-x-3">
                            <button class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50" id="cancel-btn">
                                Annuler
                            </button>
                            <button class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700" id="confirm-btn">
                                Confirmer
                            </button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            modal.querySelector('#cancel-btn').addEventListener('click', () => {
                modal.remove();
                resolve(false);
            });

            modal.querySelector('#confirm-btn').addEventListener('click', () => {
                modal.remove();
                resolve(true);
            });
        });
    }
};

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    // Vérifier l'authentification sur les pages protégées
    if (window.location.pathname !== '/login' &&
        window.location.pathname !== '/' &&
        !Auth.isAuthenticated()) {
        window.location.href = '/login';
    }

    // Initialiser les tooltips
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(function (element) {
        element.addEventListener('mouseenter', function () {
            const tooltip = document.createElement('div');
            tooltip.className = 'absolute z-10 px-2 py-1 text-xs text-white bg-gray-900 rounded shadow-lg';
            tooltip.textContent = this.dataset.tooltip;

            const rect = this.getBoundingClientRect();
            tooltip.style.top = (rect.top - 30) + 'px';
            tooltip.style.left = (rect.left + rect.width / 2) + 'px';
            tooltip.style.transform = 'translateX(-50%)';

            this.appendChild(tooltip);
        });

        element.addEventListener('mouseleave', function () {
            const tooltip = this.querySelector('.absolute');
            if (tooltip) {
                tooltip.remove();
            }
        });
    });
});