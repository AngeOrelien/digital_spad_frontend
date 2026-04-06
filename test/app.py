from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from functools import wraps
import requests
import os
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'spad-secret-key-12345')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['API_BASE_URL'] = os.environ.get('API_BASE_URL', 'http://localhost:5000/api')
app.config['ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

def login_required(f):
    """Décorateur pour vérifier l'authentification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Décorateur pour vérifier le rôle"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                return redirect(url_for('login'))
            if session['user_role'] not in roles:
                flash("Vous n'avez pas les permissions nécessaires", "error")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_api_headers():
    """Retourne les headers pour les requêtes API"""
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    if 'auth_token' in session:
        headers['Authorization'] = f"Bearer {session['auth_token']}"
    return headers

def make_api_request(method, endpoint, data=None):
    """Faire une requête à l'API backend"""
    api_url = f"{app.config['API_BASE_URL']}/{endpoint}"
    headers = get_api_headers()
    
    try:
        if method == 'GET':
            response = requests.get(api_url, headers=headers, params=data)
        elif method == 'POST':
            response = requests.post(api_url, json=data, headers=headers)
        elif method == 'PUT':
            response = requests.put(api_url, json=data, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(api_url, headers=headers)
        else:
            return None, "Méthode non autorisée"
        
        return response, None
    except requests.exceptions.ConnectionError:
        return None, "Impossible de se connecter à l'API backend"
    except Exception as e:
        return None, str(e)

@app.route('/')
def index():
    """Page d'accueil/presentation SPAD"""
    return render_template('pages/index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Connexion à l'API backend
        login_data = {
            'email': email,
            'password': password
        }
        
        response, error = make_api_request('POST', 'authentification/connexion', login_data)
        
        if error:
            return render_template('auth/login.html', error=error)
        
        if response and response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                user_data = data.get('user', {})
                session['user_id'] = user_data.get('id')
                session['user_email'] = user_data.get('email')
                session['user_role'] = user_data.get('role')
                session['user_name'] = user_data.get('name') or user_data.get('prenom', 'Utilisateur')
                session['auth_token'] = data.get('token')
                session['logged_in'] = True
                
                flash("Connexion réussie!", "success")
                return redirect(url_for('dashboard'))
            else:
                return render_template('auth/login.html', error=data.get('message', 'Identifiants incorrects'))
        else:
            error_msg = "Erreur de connexion"
            if response:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = f"Erreur {response.status_code}"
            return render_template('auth/login.html', error=error_msg)
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    """Déconnexion"""
    # Appeler l'API de déconnexion si nécessaire
    response, _ = make_api_request('POST', 'authentification/deconnexion')
    
    # Nettoyer la session
    session.clear()
    flash("Vous avez été déconnecté avec succès", "info")
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription"""
    if request.method == 'POST':
        data = {
            'nom_utilisateur': request.form.get('username'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'confirm_password': request.form.get('confirm_password'),
            'prenom': request.form.get('first_name'),
            'nom': request.form.get('last_name'),
            'telephone': request.form.get('phone'),
            'role': request.form.get('role', 'patient')
        }
        
        # Validation des mots de passe
        if data['password'] != data['confirm_password']:
            return render_template('auth/register.html', error="Les mots de passe ne correspondent pas")
        
        response, error = make_api_request('POST', 'utilisateurs/', data)
        
        if error:
            return render_template('auth/register.html', error=error)
        
        if response and response.status_code == 201:
            data = response.json()
            if data.get('success'):
                flash("Compte créé avec succès! Vous pouvez maintenant vous connecter.", "success")
                return redirect(url_for('login'))
            else:
                return render_template('auth/register.html', error=data.get('message', 'Erreur lors de la création'))
        else:
            error_msg = "Erreur lors de l'inscription"
            if response:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = f"Erreur {response.status_code}"
            return render_template('auth/register.html', error=error_msg)
    
    return render_template('auth/register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Mot de passe oublié"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        response, error = make_api_request('POST', 'auth/forgot-password', {'email': email})
        
        if error:
            return render_template('auth/forgot_password.html', error=error)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('success'):
                flash("Un email de réinitialisation a été envoyé", "success")
                return redirect(url_for('login'))
            else:
                return render_template('auth/forgot_password.html', error=data.get('message', 'Erreur'))
        else:
            return render_template('auth/forgot_password.html', 
                                 error="Erreur lors de la demande de réinitialisation")
    
    return render_template('auth/forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Réinitialisation du mot de passe"""
    if request.method == 'POST':
        data = {
            'token': token,
            'new_password': request.form.get('new_password'),
            'confirm_password': request.form.get('confirm_password')
        }
        
        if data['new_password'] != data['confirm_password']:
            return render_template('auth/reset_password.html', token=token, 
                                 error="Les mots de passe ne correspondent pas")
        
        response, error = make_api_request('POST', 'auth/reset-password', data)
        
        if error:
            return render_template('auth/reset_password.html', token=token, error=error)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get('success'):
                flash("Mot de passe réinitialisé avec succès!", "success")
                return redirect(url_for('login'))
            else:
                return render_template('auth/reset_password.html', token=token,
                                     error=data.get('message', 'Erreur'))
        else:
            return render_template('auth/reset_password.html', token=token,
                                 error="Erreur lors de la réinitialisation")
    
    return render_template('auth/reset_password.html', token=token)

@app.route('/dashboard')
@login_required
def dashboard():
    """Route principale du dashboard selon le rôle"""
    role = session.get('user_role')
    
    if role == 'patient':
        return redirect(url_for('patient_dashboard'))
    elif role == 'prestataire':
        return redirect(url_for('provider_dashboard'))
    elif role == 'medecin':
        return redirect(url_for('doctor_dashboard'))
    elif role == 'chef_secteur':
        return redirect(url_for('sector_chief_dashboard'))
    elif role == 'administrateur':
        return redirect(url_for('admin_dashboard'))
    else:
        flash("Rôle utilisateur non reconnu", "error")
        return redirect(url_for('logout'))

# ============ DASHBOARDS ============

@app.route('/dashboard/patient')
@login_required
@role_required('patient')
def patient_dashboard():
    """Dashboard patient"""
    # Récupérer les données du patient depuis l'API
    patient_id = session.get('user_id')
    response, error = make_api_request('GET', f'utilisateurs/{patient_id}')
    
    if error:
        flash(f"Erreur: {error}", "error")
        return render_template('dashboards/patient/index.html', user_data={})
    
    if response and response.status_code == 200:
        data = response.json()
        user_data = data.get('resultat', {}) if data.get('success') else {}
    else:
        user_data = {}
    
    return render_template('dashboards/patient/index.html', user_data=user_data)

@app.route('/dashboard/prestataire')
@login_required
@role_required('prestataire')
def provider_dashboard():
    """Dashboard prestataire"""
    return render_template('dashboards/provider/index.html')

@app.route('/dashboard/medecin')
@login_required
@role_required('medecin')
def doctor_dashboard():
    """Dashboard médecin"""
    return render_template('dashboards/doctor/index.html')

@app.route('/dashboard/chef-secteur')
@login_required
@role_required('chef_secteur')
def sector_chief_dashboard():
    """Dashboard chef de secteur"""
    return render_template('dashboards/sector_chief/index.html')

@app.route('/dashboard/admin')
@login_required
@role_required('administrateur')
def admin_dashboard():
    """Dashboard administrateur"""
    return render_template('dashboards/admin/index.html')

# ============ ROUTES ADMIN ============

@app.route('/admin/users')
@login_required
@role_required('administrateur')
def admin_users():
    """Gestion des utilisateurs"""
    response, error = make_api_request('GET', 'utilisateurs/')
    
    if error:
        flash(f"Erreur: {error}", "error")
        users = []
    elif response and response.status_code == 200:
        data = response.json()
        users = data.get('resultats', []) if data.get('success') else []
    else:
        users = []
    
    return render_template('dashboards/admin/users.html', users=users)

@app.route('/admin/patients')
@login_required
@role_required('administrateur')
def admin_patients():
    """Gestion des patients"""
    response, error = make_api_request('GET', 'utilisateurs/role/patient')
    
    if error:
        flash(f"Erreur: {error}", "error")
        patients = []
    elif response and response.status_code == 200:
        data = response.json()
        patients = data.get('resultats', []) if data.get('success') else []
    else:
        patients = []
    
    return render_template('dashboards/admin/patients.html', patients=patients)

@app.route('/admin/staff')
@login_required
@role_required('administrateur')
def admin_staff():
    """Gestion du personnel"""
    roles = ['prestataire', 'medecin', 'chef_secteur']
    all_staff = []
    
    for role in roles:
        response, error = make_api_request('GET', f'utilisateurs/role/{role}')
        if not error and response and response.status_code == 200:
            data = response.json()
            staff = data.get('resultats', []) if data.get('success') else []
            for person in staff:
                person['role_display'] = role.capitalize()
            all_staff.extend(staff)
    
    return render_template('dashboards/admin/staff.html', staff=all_staff)

@app.route('/admin/planning')
@login_required
@role_required('administrateur')
def admin_planning():
    """Planification"""
    return render_template('dashboards/admin/planning.html')

@app.route('/admin/statistics')
@login_required
@role_required('administrateur')
def admin_statistics():
    """Statistiques"""
    return render_template('dashboards/admin/statistics.html')

@app.route('/admin/global-alerts')
@login_required
@role_required('administrateur')
def admin_global_alerts():
    """Alertes globales"""
    response, error = make_api_request('GET', 'alertes/')
    
    if error:
        flash(f"Erreur: {error}", "error")
        alerts = []
    elif response and response.status_code == 200:
        data = response.json()
        alerts = data.get('alertes', []) if data.get('success') else []
    else:
        alerts = []
    
    return render_template('dashboards/admin/global_alerts.html', alerts=alerts)

@app.route('/admin/system-settings')
@login_required
@role_required('administrateur')
def admin_system_settings():
    """Paramètres système"""
    return render_template('dashboards/admin/system_settings.html')

@app.route('/admin/audit-logs')
@login_required
@role_required('administrateur')
def admin_audit_logs():
    """Audit & logs"""
    return render_template('dashboards/admin/audit_logs.html')

# ============ ROUTES PARTAGÉES ============

@app.route('/messages')
@login_required
def messages():
    """Page de messagerie"""
    return render_template('shared/messages.html')

@app.route('/calendar')
@login_required
def calendar():
    """Page agenda/calendrier"""
    return render_template('shared/calendar.html')

@app.route('/notifications')
@login_required
def notifications():
    """Page notifications"""
    return render_template('shared/notifications.html')

@app.route('/help')
@login_required
def help_support():
    """Page aide & support"""
    return render_template('shared/help_support.html')

@app.route('/profile')
@login_required
def profile():
    """Page profil utilisateur"""
    user_id = session.get('user_id')
    response, error = make_api_request('GET', f'utilisateurs/{user_id}')
    
    if error:
        flash(f"Erreur: {error}", "error")
        user_data = {}
    elif response and response.status_code == 200:
        data = response.json()
        user_data = data.get('resultat', {}) if data.get('success') else {}
    else:
        user_data = {}
    
    return render_template('shared/profile.html', user_data=user_data)

# ============ CONTEXT PROCESSORS ============

@app.context_processor
def inject_user():
    """Injecte les informations utilisateur dans tous les templates"""
    user_data = {
        'is_authenticated': 'user_id' in session,
        'user_id': session.get('user_id'),
        'user_email': session.get('user_email'),
        'user_role': session.get('user_role'),
        'user_name': session.get('user_name'),
        'current_year': datetime.now().year
    }
    return user_data

@app.context_processor
def inject_config():
    """Injecte la configuration"""
    return {
        'api_base_url': app.config['API_BASE_URL']
    }

# ============ ERROR HANDLERS ============

# @app.errorhandler(404)
# def not_found_error(error):
#     return render_template('errors/404.html'), 404

# @app.errorhandler(500)
# def internal_error(error):
#     return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)