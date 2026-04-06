class AuthManager {
    constructor() {
        this.apiBaseUrl = '/api';  // Utiliser le proxy
        this.initEventListeners();
        this.checkAuthStatus();
    }

    initEventListeners() {
        // Toggle password visibility
        document.querySelectorAll('.password-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                this.togglePassword(e.target.closest('.password-toggle'));
            });
        });

        // Form submission
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Register form
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }
    }

    async handleLogin(event) {
        event.preventDefault();

        const form = event.target;
        const submitBtn = form.querySelector('#submitBtn');
        const submitText = form.querySelector('#submitText');
        const loadingSpinner = form.querySelector('#loadingSpinner');

        // Récupérer les données du formulaire - CORRIGÉ pour utiliser les noms français
        const formData = new FormData(form);
        const data = {
            email: formData.get('email'),
            mot_de_passe: formData.get('password')  // Nom en français
        };

        // Validation
        if (!data.email || !data.mot_de_passe) {
            this.showError('Veuillez remplir tous les champs requis');
            return;
        }

        // Désactiver le bouton pendant la requête
        this.setLoadingState(submitBtn, submitText, loadingSpinner, true);

        try {
            // Appel API - CORRIGÉ l'endpoint
            const response = await fetch(`${this.apiBaseUrl}/authentification/connexion`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Connexion réussie
                this.showSuccess('Connexion réussie !');

                // Rediriger vers le dashboard
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1000);

            } else {
                // Erreur de connexion
                this.showError(result.message || 'Identifiants incorrects');
                this.setLoadingState(submitBtn, submitText, loadingSpinner, false);
            }

        } catch (error) {
            console.error('Erreur de connexion:', error);
            this.showError('Erreur de connexion au serveur');
            this.setLoadingState(submitBtn, submitText, loadingSpinner, false);
        }
    }

    async handleRegister(event) {
        event.preventDefault();

        const form = event.target;
        const submitBtn = form.querySelector('#submitBtn');
        const submitText = form.querySelector('#submitText');
        const loadingSpinner = form.querySelector('#loadingSpinner');

        // Récupérer les données du formulaire - CORRIGÉ pour utiliser les noms français
        const formData = new FormData(form);
        const data = {
            nom_utilisateur: formData.get('username'),
            email: formData.get('email'),
            mot_de_passe: formData.get('password'),  // Nom en français
            prenom: formData.get('first_name'),
            nom: formData.get('last_name'),
            telephone: formData.get('phone'),
            role: formData.get('role', 'patient')
        };

        // Validation
        const errors = this.validateRegistration(data);
        if (errors.length > 0) {
            this.showError(errors.join('<br>'));
            return;
        }

        // Vérifier la confirmation du mot de passe
        const confirmPassword = formData.get('confirm_password');
        if (data.mot_de_passe !== confirmPassword) {
            this.showError('Les mots de passe ne correspondent pas');
            return;
        }

        // Si c'est un patient, ajouter les détails
        if (data.role === 'patient') {
            data.details_patient = {
                date_naissance: formData.get('birth_date') || '',
                sexe: formData.get('gender') || '',
                adresse: formData.get('address') || ''
            };
        }

        // Désactiver le bouton pendant la requête
        this.setLoadingState(submitBtn, submitText, loadingSpinner, true);

        try {
            // Appel API - CORRIGÉ l'endpoint
            const response = await fetch(`${this.apiBaseUrl}/authentification/inscription`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Inscription réussie
                this.showSuccess('Compte créé avec succès !');

                // Rediriger vers la page de connexion
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);

            } else {
                // Erreur d'inscription
                this.showError(result.message || 'Erreur lors de la création du compte');
                this.setLoadingState(submitBtn, submitText, loadingSpinner, false);
            }

        } catch (error) {
            console.error('Erreur d\'inscription:', error);
            this.showError('Erreur de connexion au serveur');
            this.setLoadingState(submitBtn, submitText, loadingSpinner, false);
        }
    }

    togglePassword(toggleButton) {
        const inputId = toggleButton.getAttribute('data-target');
        const passwordInput = document.getElementById(inputId);
        const eyeIcon = toggleButton.querySelector('i');

        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            eyeIcon.classList.remove('fa-eye');
            eyeIcon.classList.add('fa-eye-slash');
            toggleButton.setAttribute('title', 'Masquer le mot de passe');
        } else {
            passwordInput.type = 'password';
            eyeIcon.classList.remove('fa-eye-slash');
            eyeIcon.classList.add('fa-eye');
            toggleButton.setAttribute('title', 'Afficher le mot de passe');
        }
    }

    validateRegistration(data) {
        const errors = [];

        if (!data.nom_utilisateur || data.nom_utilisateur.length < 3) {
            errors.push('Le nom d\'utilisateur doit contenir au moins 3 caractères');
        }

        if (!data.email || !this.isValidEmail(data.email)) {
            errors.push('Veuillez entrer une adresse email valide');
        }

        if (!data.mot_de_passe || data.mot_de_passe.length < 8) {
            errors.push('Le mot de passe doit contenir au moins 8 caractères');
        }

        if (!data.prenom) {
            errors.push('Le prénom est requis');
        }

        return errors;
    }

    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    setLoadingState(button, textElement, spinnerElement, isLoading) {
        if (isLoading) {
            button.disabled = true;
            if (textElement) textElement.textContent = 'Traitement en cours...';
            if (spinnerElement) spinnerElement.classList.remove('hidden');
        } else {
            button.disabled = false;
            if (textElement) textElement.textContent = button.getAttribute('data-original-text') || 'Valider';
            if (spinnerElement) spinnerElement.classList.add('hidden');
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type = 'info') {
        // Supprimer les notifications existantes
        document.querySelectorAll('.auth-notification').forEach(notification => {
            notification.remove();
        });

        const colors = {
            success: 'bg-green-500 border-green-600',
            error: 'bg-red-500 border-red-600',
            info: 'bg-blue-500 border-blue-600',
            warning: 'bg-yellow-500 border-yellow-600'
        };

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            info: 'fa-info-circle',
            warning: 'fa-exclamation-triangle'
        };

        const notification = document.createElement('div');
        notification.className = `auth-notification fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg animate-fade-in z-50 border-l-4`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${icons[type]} mr-3 text-lg"></i>
                <div>${message}</div>
                <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-suppression après 5 secondes
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    checkAuthStatus() {
        // Vérifier si l'utilisateur est déjà connecté
        // On utilise maintenant la session Flask
    }
}

// Initialiser le gestionnaire d'authentification
document.addEventListener('DOMContentLoaded', () => {
    window.authManager = new AuthManager();

    // Auto-focus sur le premier champ de formulaire
    const firstInput = document.querySelector('input[type="email"], input[type="text"]');
    if (firstInput) {
        firstInput.focus();
    }
});