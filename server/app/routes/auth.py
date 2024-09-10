from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from ..forms.forms import RegistrationForm, LoginForm
from ..models.models import User
from ..extensions import db,login_manager
from passlib.hash import sha256_crypt
from sqlalchemy.exc import IntegrityError



auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role == 'admin':
        form = RegistrationForm()
        if form.validate_on_submit():
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Ce nom d\'utilisateur est déjà pris. Veuillez choisir un autre.', 'danger')
                return render_template('register.html', form=form)

            hashed_password = sha256_crypt.hash(form.password.data)
            new_user = User(username=form.username.data, password=hashed_password, role=form.role.data)
            db.session.add(new_user)

            try:
                db.session.commit()
                flash('Compte créé avec succès!', 'success')
                return redirect(url_for('auth.login'))
            except IntegrityError:
                db.session.rollback()
                flash('Erreur lors de la création du compte. Veuillez réessayer.', 'danger')

        return render_template('register.html', form=form)

    else:
        flash('Vous n\'êtes pas autorisé à enregistrer un utilisateur.', 'danger')
        return redirect(url_for('gallery.gallery'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and sha256_crypt.verify(form.password.data, user.password):
            login_user(user)
            flash('Connexion avec succès !', 'success')
            return redirect(url_for('gallery.dashboard'))
        else:
            flash("Echec de connexion. Verifier votre nom d'utilisateur ou votre mot de passe.", 'danger')
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté avec succès!', 'success')
    return redirect(url_for('auth.login'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
