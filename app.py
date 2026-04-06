from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from functools import wraps
import requests
import os
from datetime import datetime
import json

app = Flask(__name__,
            static_folder='static',
            template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', 'spad-secret-key-12345')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['API_BASE_URL'] = os.environ.get('API_BASE_URL', 'http://localhost:5000/api')
app.config['ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ============ ROUTES POUR LES FICHIERS STATICS ============

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/static/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(app.static_folder, 'css'), filename)

@app.route('/static/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(app.static_folder, 'js'), filename)

@app.route('/static/images/<path:filename>')
def serve_images(filename):
    return send_from_directory(os.path.join(app.static_folder, 'images'), filename)


# ============ ROUTES API PROXY ============

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proxy(path):
    """Proxy pour les appels API vers le backend"""
    url = f"{app.config['API_BASE_URL']}/{path}"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Ajouter les cookies de session si disponibles
    if 'utilisateur_id' in session:
        # Vous pouvez ajouter un token d'authentification si nécessaire
        pass
    
    try:
        if request.method == 'GET':
            response = requests.get(url, headers=headers, params=request.args)
        elif request.method == 'POST':
            response = requests.post(url, headers=headers, json=request.json)
        elif request.method == 'PUT':
            response = requests.put(url, headers=headers, json=request.json)
        elif request.method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            return jsonify({'success': False, 'message': 'Method not allowed'}), 405
        
        # Retourner la réponse du backend
        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'message': 'Cannot connect to backend API'}), 502
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    

def login_required(f):
    """Décorateur pour vérifier l'authentification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'utilisateur_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Décorateur pour vérifier le rôle"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'utilisateur_role' not in session:
                return redirect(url_for('login'))
            if session['utilisateur_role'] not in roles:
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
            response = requests.delete(api_url, json=data, headers=headers)
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
        mot_de_passe = request.form.get('password')
        
        # Connexion à l'API backend - CORRIGÉ pour correspondre au backend
        login_data = {
            'email': email,
            'mot_de_passe': mot_de_passe  # Nom en français comme dans le backend
        }
        
        response, error = make_api_request('POST', 'authentification/connexion', login_data)
        
        if error:
            return render_template('auth/login.html', error=error)
        
        if response and response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                utilisateur_data = data.get('resultats', {})
                session['utilisateur_id'] = utilisateur_data.get('id')
                session['utilisateur_email'] = utilisateur_data.get('email')
                session['utilisateur_role'] = utilisateur_data.get('role')
                session['utilisateur_nom'] = utilisateur_data.get('nom', '')
                session['utilisateur_prenom'] = utilisateur_data.get('prenom', 'Utilisateur')
                session['utilisateur_nom_utilisateur'] = utilisateur_data.get('nom_utilisateur', '')
                session['logged_in'] = True
                
                # Stocker les détails patient si disponible
                if data.get('details_patient'):
                    session['details_patient'] = data.get('details_patient')
                
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
    # Appeler l'API de déconnexion
    response, _ = make_api_request('POST', 'authentification/deconnexion')
    
    # Nettoyer la session
    session.clear()
    flash("Vous avez été déconnecté avec succès", "info")
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription"""
    if request.method == 'POST':
        # Préparer les données pour l'API backend - CORRIGÉ
        data = {
            'nom_utilisateur': request.form.get('username'),
            'email': request.form.get('email'),
            'mot_de_passe': request.form.get('password'),  # Nom en français
            'prenom': request.form.get('first_name'),
            'nom': request.form.get('last_name'),
            'telephone': request.form.get('phone'),
            'role': request.form.get('role', 'patient')
        }
        
        # Validation des mots de passe
        confirm_password = request.form.get('confirm_password')
        if data['mot_de_passe'] != confirm_password:
            return render_template('auth/register.html', error="Les mots de passe ne correspondent pas")
        
        # Si c'est un patient, ajouter les détails
        if data['role'] == 'patient':
            data['details_patient'] = {
                'date_naissance': request.form.get('birth_date', ''),
                'sexe': request.form.get('gender', ''),
                'adresse': request.form.get('address', '')
            }
        
        response, error = make_api_request('POST', 'authentification/inscription', data)
        
        if error:
            return render_template('auth/register.html', error=error)
        
        if response:
            response_data = response.json()
            if response.status_code == 201 and response_data.get('success'):
                flash("Compte créé avec succès! Vous pouvez maintenant vous connecter.", "success")
                return redirect(url_for('login'))
            else:
                return render_template('auth/register.html', 
                                    error=response_data.get('message', 'Erreur lors de la création'))
        else:
            return render_template('auth/register.html', error="Erreur lors de l'inscription")
    
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

@app.route('/dashboard')
@login_required
def dashboard():
    """Route principale du dashboard selon le rôle"""
    role = session.get('utilisateur_role')
    
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

# ============ DASHBOARDS ============

@app.route('/dashboard/patient')
@login_required
@role_required('patient')
def patient_dashboard():
    """Dashboard patient"""
    # Récupérer les données du patient depuis l'API
    utilisateur_id = session.get('utilisateur_id')
    response, error = make_api_request('GET', 'authentification/profil')
    
    if error:
        flash(f"Erreur: {error}", "error")
        utilisateur_data = {}
    elif response and response.status_code == 200:
        data = response.json()
        utilisateur_data = data.get('resultats', {}) if data.get('success') else {}
    else:
        utilisateur_data = {}
    
    return render_template('dashboards/patient/index.html', utilisateur_data=utilisateur_data)

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
        utilisateurs = []
    elif response and response.status_code == 200:
        data = response.json()
        utilisateurs = data.get('resultats', []) if data.get('success') else []
    else:
        utilisateurs = []
    
    return render_template('dashboards/admin/users.html', utilisateurs=utilisateurs)

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

@app.route('/admin/secteurs')
@login_required
@role_required('administrateur')
def admin_secteurs():
    """Gestion des secteurs"""
    response, error = make_api_request('GET', 'secteurs/')
    
    if error:
        flash(f"Erreur: {error}", "error")
        secteurs = []
    elif response and response.status_code == 200:
        data = response.json()
        secteurs = data.get('secteurs', []) if data.get('success') else []
    else:
        secteurs = []
    
    return render_template('dashboards/admin/secteurs.html', secteurs=secteurs)

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

# ... (autres routes admin restent similaires avec les noms en français)

# ============ CONTEXT PROCESSORS ============

@app.context_processor
def inject_user():
    """Injecte les informations utilisateur dans tous les templates"""
    user_data = {
        'is_authenticated': 'utilisateur_id' in session,
        'utilisateur_id': session.get('utilisateur_id'),
        'utilisateur_email': session.get('utilisateur_email'),
        'utilisateur_role': session.get('utilisateur_role'),
        'utilisateur_nom': session.get('utilisateur_nom'),
        'utilisateur_prenom': session.get('utilisateur_prenom'),
        'utilisateur_nom_utilisateur': session.get('utilisateur_nom_utilisateur'),
        'current_year': datetime.now().year
    }
    return user_data

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)