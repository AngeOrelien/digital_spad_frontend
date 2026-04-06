import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'spad-dev-key-2024')
    SESSION_COOKIE_NAME = 'spad_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # True en production avec HTTPS
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Configuration API backend
    API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5000/api')
    
    # Configuration uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    
    # Rôles disponibles
    ROLES = {
        'patient': 'Patient',
        'prestataire': 'Prestataire',
        'medecin': 'Médecin',
        'chef_secteur': 'Chef de Secteur',
        'administrateur': 'Administrateur'
    }
    
    # Chemins des templates par rôle
    DASHBOARD_TEMPLATES = {
        'patient': 'dashboards/patient/index.html',
        'prestataire': 'dashboards/provider/index.html',
        'medecin': 'dashboards/doctor/index.html',
        'chef_secteur': 'dashboards/sector_chief/index.html',
        'administrateur': 'dashboards/admin/index.html'
    }

class DevelopmentConfig(Config):
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}