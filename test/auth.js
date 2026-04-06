/**
 * Utilitaires d'authentification SPAD
 */

const Auth = {
    // Configuration
    config: {
        apiBaseUrl: window.location.origin + '/api/proxy',
        tokenKey: 'spad_token',
        userKey: 'spad_user'
    },

    // Vérifier si l'utilisateur est connecté
    isAuthenticated() {
        return !!localStorage.getItem(this.config.tokenKey);
    },

    // Récupérer les informations de l'utilisateur
    getUser() {
        const user = localStorage.getItem(this.config.userKey);
        return user ? JSON.parse(user) : null;
    },

    // Récupérer le token
    getToken() {
        return localStorage.getItem(this.config.tokenKey);
    },

    // Récupérer le rôle de l'utilisateur
    getUserRole() {
        const user = this.getUser();
        return user ? user.role : null;
    },

    // Vérifier les permissions
    hasRole(role) {
        const userRole = this.getUserRole();
        return userRole === role;
    },

    hasAnyRole(roles) {
        const userRole = this.getUserRole();
        return roles.includes(userRole);
    },

    // Sauvegarder l'authentification
    saveAuth(token, user) {
        localStorage.setItem(this.config.tokenKey, token);
        localStorage.setItem(this.config.userKey, JSON.stringify(user));
    },

    // Nettoyer l'authentification
    clearAuth() {
        localStorage.removeItem(this.config.tokenKey);
        localStorage.removeItem(this.config.userKey);
    },

    // Vérifier et rediriger si non authentifié
    requireAuth(redirectTo = '/login') {
        if (!this.isAuthenticated()) {
            window.location.href = redirectTo;
            return false;
        }
        return true;
    },

    // Vérifier le rôle et rediriger
    requireRole(role, redirectTo = '/dashboard') {
        if (!this.isAuthenticated()) {
            window.location.href = '/login';
            return false;
        }

        if (!this.hasRole(role)) {
            window.location.href = redirectTo;
            return false;
        }

        return true;
    },

    // Gestion des headers d'authentification
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    },

    // Intercepter les erreurs d'authentification
    handleAuthError(error) {
        console.error('Erreur d\'authentification:', error);

        // Si le token est invalide ou expiré, déconnecter l'utilisateur
        if (error.status === 401) {
            this.logout();
            return true;
        }

        return false;
    },

    // Déconnexion
    async logout() {
        try {
            await fetch(`${this.config.apiBaseUrl}/authentification/deconnexion`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });
        } catch (error) {
            console.error('Erreur lors de la déconnexion:', error);
        } finally {
            this.clearAuth();
            window.location.href = '/login';
        }
    },

    // Rafraîchir le token
    async refreshToken() {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}/auth/refresh`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.token) {
                    this.saveAuth(data.token, this.getUser());
                    return true;
                }
            }
        } catch (error) {
            console.error('Erreur lors du rafraîchissement du token:', error);
        }

        return false;
    },

    // Vérifier la validité du token
    async checkTokenValidity() {
        if (!this.isAuthenticated()) {
            return false;
        }

        try {
            const response = await fetch(`${this.config.apiBaseUrl}/auth/validate`, {
                headers: this.getAuthHeaders()
            });

            return response.ok;
        } catch (error) {
            return false;
        }
    },

    // Middleware pour les requêtes API
    async apiRequest(url, options = {}) {
        const defaultOptions = {
            headers: this.getAuthHeaders()
        };

        const finalOptions = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, finalOptions);

            // Gérer les erreurs d'authentification
            if (response.status === 401) {
                // Essayer de rafraîchir le token
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    // Réessayer la requête avec le nouveau token
                    finalOptions.headers = this.getAuthHeaders();
                    return await fetch(url, finalOptions);
                } else {
                    // Déconnexion si le rafraîchissement échoue
                    this.logout();
                    throw new Error('Session expirée');
                }
            }

            return response;
        } catch (error) {
            if (this.handleAuthError(error)) {
                throw new Error('Session expirée. Veuillez vous reconnecter.');
            }
            throw error;
        }
    },

    // Initialisation
    init() {
        // Vérifier l'authentification au chargement de la page
        this.checkAuthOnPageLoad();

        // Intercepter les erreurs d'authentification globalement
        this.setupErrorHandling();

        // Configurer le bouton de déconnexion
        this.setupLogoutButton();
    },

    checkAuthOnPageLoad() {
        const publicPages = ['/', '/login', '/register', '/forgot-password', '/reset-password'];
        const currentPath = window.location.pathname;

        // Si l'utilisateur est sur une page protégée mais non authentifié
        if (!publicPages.includes(currentPath) && !this.isAuthenticated()) {
            window.location.href = '/login';
            return;
        }

        // Si l'utilisateur est déjà connecté et tente d'accéder aux pages d'authentification
        if (this.isAuthenticated() &&
            ['/login', '/register'].includes(currentPath)) {
            window.location.href = '/dashboard';
        }
    },

    setupErrorHandling() {
        // Intercepter les erreurs globales
        window.addEventListener('error', (event) => {
            if (event.error && event.error.message.includes('401')) {
                this.logout();
            }
        });

        // Intercepter les réponses fetch non authentifiées
        const originalFetch = window.fetch;
        window.fetch = async function (...args) {
            const response = await originalFetch(...args);

            if (response.status === 401) {
                Auth.logout();
            }

            return response;
        };
    },

    setupLogoutButton() {
        // Trouver tous les boutons de déconnexion
        document.querySelectorAll('[data-action="logout"]').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        });
    },

    // Utilitaires UI
    showAuthNotification(message, type = 'info') {
        // Créer ou mettre à jour une notification
        let notification = document.getElementById('auth-notification');

        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'auth-notification';
            notification.className = 'fixed z-50 top-4 right-4';
            document.body.appendChild(notification);
        }

        const colors = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            info: 'bg-blue-500 text-white',
            warning: 'bg-yellow-500 text-white'
        };

        notification.innerHTML = `
            <div class="${colors[type]} px-6 py-3 rounded-lg shadow-lg animate-fade-in">
                <div class="flex items-center">
                    <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'} mr-3"></i>
                    <span>${message}</span>
                    <button class="ml-4 hover:opacity-75" onclick="this.parentElement.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;

        // Auto-suppression après 5 secondes
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    },

    // Gestion des sessions
    startSessionTimer() {
        // Détecter l'inactivité de l'utilisateur
        let timeout;

        const resetTimer = () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                // Après 30 minutes d'inactivité, déconnecter
                if (this.isAuthenticated()) {
                    this.showAuthNotification('Session expirée par inactivité', 'warning');
                    this.logout();
                }
            }, 30 * 60 * 1000); // 30 minutes
        };

        // Réinitialiser le timer sur les interactions utilisateur
        ['click', 'mousemove', 'keypress', 'scroll'].forEach(event => {
            document.addEventListener(event, resetTimer);
        });

        resetTimer();
    }
};

// Initialiser l'authentification
document.addEventListener('DOMContentLoaded', () => {
    Auth.init();
});

// Exposer Auth globalement
window.Auth = Auth;