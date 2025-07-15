from flask import Blueprint
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_login import current_user
from wtforms import PasswordField, SelectField
from passlib.hash import sha256_crypt
from ..extensions import db
from ..models.models import User, Photo

admin_bp = Blueprint('admin', __name__)

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin():
            return self.render('admin/index.html')
        return super().index()

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()

class UserAdminView(ModelView):
    column_list = ('username', 'role')
    form_base_class = SecureForm

    # On laisse Flask-Admin générer les champs à partir du modèle
    form_excluded_columns = ('photos',)

    def scaffold_form(self):
        form_class = super().scaffold_form()
        
        # Remplace le champ role par un SelectField
        form_class.role = SelectField('Role', choices=[('standard', 'Standard'), ('admin', 'Admin')])
        
        # Ajoute un champ password (non stocké tel quel dans la base, on va le traiter dans on_model_change)
        form_class.password = PasswordField('Password')
        return form_class

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.set_password(form.password.data)
        elif not is_created:
            # Conserver l’ancien mot de passe si champ vide
            existing_user = db.session.get(User, model.id)
            model.password = existing_user.password

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()

class PhotoAdminView(ModelView):
    column_list = ('user_id', 'image', 'date_posted')
    form_columns = ('user_id', 'image', 'date_posted')

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()

# Enregistrement des vues
admin = Admin(index_view=MyAdminIndexView())
admin.add_view(UserAdminView(User, db.session))
admin.add_view(PhotoAdminView(Photo, db.session))
