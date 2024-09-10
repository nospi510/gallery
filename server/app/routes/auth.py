from flask import Blueprint, jsonify, render_template, request, url_for
from flask_login import login_user, login_required, logout_user, current_user
from ..forms.forms import RegistrationForm, LoginForm
from ..models.models import User
from ..extensions import db, login_manager
from passlib.hash import sha256_crypt
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Vérification que le Content-Type est bien JSON
        if request.content_type != 'application/json':
            return jsonify({"error": "Content-Type must be application/json"}), 415

        # Récupérer les données JSON du corps de la requête
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        # Validation des informations de connexion
        user = User.query.filter_by(username=username).first()
        if user and sha256_crypt.verify(password, user.password):
            login_user(user)
            return jsonify({
                "message": "Connexion réussie",
                "status": "success",
                "redirect": url_for('gallery.dashboard') 
            }), 200
        else:
            return jsonify({"message": "Echec de connexion. Vérifiez vos identifiants", "status": "error"}), 401

    # Pour les requêtes GET, retournez le formulaire HTML
    form = LoginForm()
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role != 'admin':
        return jsonify({"message": "Non autorisé", "status": "error"}), 403

    if request.method == 'POST':
        if request.content_type != 'application/json':
            return jsonify({"error": "Content-Type must be application/json"}), 415
        
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({"message": "Ce nom d'utilisateur est déjà pris", "status": "error"}), 400

        hashed_password = sha256_crypt.hash(password)
        new_user = User(username=username, password=hashed_password, role=role)
        db.session.add(new_user)

        try:
            db.session.commit()
            return jsonify({
                "message": "Compte créé avec succès",
                "status": "success",
                "redirect": url_for('auth.login')  # Redirection vers la page de connexion
            }), 201
        except IntegrityError:
            db.session.rollback()
            return jsonify({"message": "Erreur lors de la création du compte", "status": "error"}), 500

    # Pour les requêtes GET, retournez le formulaire HTML
    form = RegistrationForm()
    return render_template('register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({
        "message": "Déconnexion réussie",
        "status": "success",
        "redirect": url_for('auth.login')  # Redirection vers la page de connexion
    }), 200


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
