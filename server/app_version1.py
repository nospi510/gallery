from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from passlib.hash import sha256_crypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import secrets
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import QueuePool
from PIL import Image
import pyheif


app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://nick:passer@192.168.1.23/gallery?charset=utf8mb4'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://nick:passer@192.168.1.30/gallery?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secrets.token_hex(24)

# Ajout de la configuration pour gérer les connexions inactives
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': QueuePool,
    'pool_size': 10,
    'max_overflow': 20,
    'pool_recycle': 10,
    'pool_pre_ping': True,
}

db = SQLAlchemy(app)


# Configurer les paramètres de session
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Durée de vie de la session (1 jour ici)
#app.config['SESSION_COOKIE_SECURE'] = True  # Les cookies de session sont transmis uniquement sur des connexions sécurisées (HTTPS)
#app.config['SESSION_COOKIE_HTTPONLY'] = True  # Empêche l'accès au cookie via JavaScript
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Spécifie la politique SameSite pour les cookies de session (peut être 'Lax' ou 'Strict')

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modèle pour la base de données
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='standard')
    photos = db.relationship('Photo', backref='author', lazy=True)

    def set_password(self, password):
        self.password = sha256_crypt.hash(password)

    def check_password(self, password):
        return sha256_crypt.verify(password, self.password)

    def is_admin(self):
        return self.role == 'admin'

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('standard', 'Standard'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255), nullable=False, default='default.jpg')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class AddPhotoForm(FlaskForm):
    image = FileField('Charger une image', validators=[FileAllowed(['jpg', 'png', 'jpeg','heic'], 'Images only!')])
    submit = SubmitField('Importer')

class EditProfileForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Nouveau Mot de Passe')
    confirm_password = PasswordField('Confirmer le Mot de Passe', validators=[EqualTo('password')])
    submit = SubmitField('Enregistrer les Modifications')

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return self.render('admin/index.html')
        return super(MyAdminIndexView, self).index()

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()

class UserAdminView(ModelView):
    column_list = ('username', 'role')
    form_columns = ('username', 'password', 'role')

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()

class PhotoAdminView(ModelView):
    column_list = ('user_id', 'image', 'date_posted')
    form_columns = ('user_id', 'image', 'date_posted')

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()

admin = Admin(app, index_view=MyAdminIndexView())
admin.add_view(UserAdminView(User, db.session))
admin.add_view(PhotoAdminView(Photo, db.session))

def convert_heic_to_jpeg(heic_file):
    heif_file = pyheif.read(heic_file)
    image = Image.frombytes(
        heif_file.mode, 
        heif_file.size, 
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride,
    )
    return image







@app.route('/register', methods=['GET', 'POST'])
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
                return redirect(url_for('login'))
            except IntegrityError:
                db.session.rollback()
                flash('Erreur lors de la création du compte. Veuillez réessayer.', 'danger')

        return render_template('register.html', form=form)

    else:
        flash('Vous n\'êtes pas autorisé à enregistrer un utilisateur.', 'danger')
        return redirect(url_for('gallery'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and sha256_crypt.verify(form.password.data, user.password):
            login_user(user)
            flash('Connexion avec succès !', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash("Echec de connexion. Verifier votre nom d'utilisateur ou votre mot de passe.", 'danger')
    return render_template('login.html', form=form)

@app.route('/', methods=['GET'])
@login_required
def gallery():
    sort_option = request.args.get('sort', 'none')
    search_query = request.args.get('search', '')

    if search_query:
        users = User.query.filter(User.username.ilike(f'%{search_query}%')).all()
    else:
        if sort_option == 'az':
            users = User.query.order_by(User.username.asc()).all()
        elif sort_option == 'za':
            users = User.query.order_by(User.username.desc()).all()
        elif sort_option == 'recent':
            users = User.query.join(Photo).group_by(User.id).order_by(func.max(Photo.date_posted).desc()).all()
        elif sort_option == 'old':
            users = User.query.join(Photo).group_by(User.id).order_by(func.max(Photo.date_posted).asc()).all()
        else:
            users = User.query.all()

    return render_template('gallery.html', users=users, sort_option=sort_option, search_query=search_query)



@app.route('/add_photo', methods=['GET', 'POST'])
@login_required
def add_photo():
    form = AddPhotoForm()
    if form.validate_on_submit():
        for uploaded_file in request.files.getlist('image'):
            if uploaded_file.filename != '':
                filename = save_photo(uploaded_file)
                new_photo = Photo(image=filename, user_id=current_user.id)
                db.session.add(new_photo)
                db.session.commit()

        flash('Photos ajoutées avec succès!', 'success')
        return redirect(url_for('gallery'))

    return render_template('add_photo.html', form=form)





def save_photo(photo):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(photo.filename)
    f_ext = f_ext.lower()
    photo_fn = random_hex + ('.jpg' if f_ext == '.heic' else f_ext)
    photo_path = os.path.join(app.root_path, 'static/images', photo_fn)

    if f_ext == '.heic':
        image = convert_heic_to_jpeg(photo)
        image.save(photo_path, 'JPEG')
    else:
        photo.save(photo_path)

    return photo_fn




@app.route('/view_photo/<int:photo_id>')
def view_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    return send_from_directory('static/images', photo.image)

@app.route('/dashboard')
@login_required
def dashboard():
    sort_order = request.args.get('sort_order', 'recent')

    if sort_order == 'recent':
        user_photos = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.date_posted.desc()).all()
    elif sort_order == 'old':
        user_photos = Photo.query.filter_by(user_id=current_user.id).order_by(Photo.date_posted.asc()).all()
    else:
        pass

    return render_template('dashboard.html', user_photos=user_photos)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()

    if form.validate_on_submit():
        current_user.username = form.username.data

        if form.password.data:
            current_user.set_password(form.password.data)

        db.session.commit()
        flash('Profil mis à jour avec succès!', 'success')
        return redirect(url_for('dashboard'))

    form.username.data = current_user.username

    return render_template('edit_profile.html', form=form)

@app.route('/get_users')
def get_users():
    users = [user.username for user in User.query.all()]
    return jsonify(users)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté avec succès!', 'success')
    return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)

