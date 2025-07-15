from flask import Blueprint, jsonify, render_template, request, url_for, redirect, flash
from flask_login import login_user, login_required, logout_user, current_user
from ..forms.forms import RegistrationForm, LoginForm
from ..models.models import User, ResetCode
from ..extensions import db, login_manager
from ..utils.utils import send_reset_code_email, generate_reset_code
from passlib.hash import sha256_crypt
from sqlalchemy.exc import IntegrityError
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.content_type != 'application/json':
            return jsonify({"error": "Content-Type must be application/json"}), 415

        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if user and sha256_crypt.verify(password, user.password):
            login_user(user)
            return jsonify({
                "message": "Connexion réussie",
                "status": "success",
                "redirect": url_for('gallery.dashboard')
            }), 200
        else:
            return jsonify({"message": "Échec de connexion. Vérifiez vos identifiants", "status": "error"}), 401

    form = LoginForm()
    return render_template('login.html', form=form)

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        if request.content_type != 'application/json':
            return jsonify({"error": "Content-Type must be application/json"}), 415

        data = request.get_json()
        username = data.get('username')
        user = User.query.filter_by(username=username).first()

        if not user:
            return jsonify({"message": "Utilisateur non trouvé", "status": "error"}), 404

        code = generate_reset_code()
        reset_code = ResetCode(user_id=user.id, code=code)
        db.session.add(reset_code)
        db.session.commit()

        if send_reset_code_email(username, code):
            return jsonify({
                "message": "Un code de réinitialisation a été envoyé à nick@visiotech.me. Veuillez contacter Nick pour obtenir le code.",
                "status": "success",
                "redirect": url_for('auth.reset_password')
            }), 200
        else:
            return jsonify({"message": "Erreur lors de l'envoi du code", "status": "error"}), 500

    return render_template('forgot_password.html')

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        if request.content_type != 'application/json':
            return jsonify({"error": "Content-Type must be application/json"}), 415

        data = request.get_json()
        username = data.get('username')
        code = data.get('code')
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password != confirm_password:
            return jsonify({"message": "Les mots de passe ne correspondent pas", "status": "error"}), 400

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"message": "Utilisateur non trouvé", "status": "error"}), 404

        reset_code = ResetCode.query.filter_by(user_id=user.id, code=code).first()
        if not reset_code or reset_code.expires_at < datetime.utcnow():
            return jsonify({"message": "Code invalide ou expiré", "status": "error"}), 400

        user.set_password(password)
        ResetCode.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        return jsonify({
            "message": "Mot de passe réinitialisé avec succès",
            "status": "success",
            "redirect": url_for('auth.login')
        }), 200

    return render_template('reset_password.html')

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
                "redirect": url_for('auth.login')
            }), 201
        except IntegrityError:
            db.session.rollback()
            return jsonify({"message": "Erreur lors de la création du compte", "status": "error"}), 500

    form = RegistrationForm()
    return render_template('register.html', form=form)

@auth_bp.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté avec succès!', 'success')
    return jsonify({
        "message": "Déconnexion réussie",
        "status": "success",
        "redirect": url_for('auth.login')
    }), 200

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))