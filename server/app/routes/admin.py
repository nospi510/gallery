from flask import Blueprint
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from ..extensions import db
from ..models.models import User, Photo

admin_bp = Blueprint('admin', __name__)

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

admin = Admin(index_view=MyAdminIndexView())
admin.add_view(UserAdminView(User, db.session))
admin.add_view(PhotoAdminView(Photo, db.session))
