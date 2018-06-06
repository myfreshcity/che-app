import flask_admin
from flask import Flask, url_for, redirect, render_template, request, abort
from flask_admin import helpers as admin_helpers
from flask_admin.contrib import sqla
from flask_babelex import Babel
from flask_security import Security, SQLAlchemyUserDatastore, \
    current_user
from flask_sqlalchemy import SQLAlchemy

# Create Flask application
from config import config

app = Flask(__name__)
app.config.from_object(config)
db = SQLAlchemy(app)

babel = Babel(app)
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'

from webapp.models import Role, User, Car

# Define models

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# Create customized model view class
class MyModelView(sqla.ModelView):

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser'):
            return True

        return False

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))

class MyModelViewUser(MyModelView):
    # column_select_related_list = ['mps',]
    column_formatters = dict(
        password=lambda v, c, m, p: '**' + m.password[-6:],
    )
    column_searchable_list = (User.email,)

class MyModelViewBrand(MyModelView):
    column_labels = dict(
        initial=u'首字母',
        full_name=u'名称',
    )
    # 如果不想显示某些字段，可以重载这个变量
    column_exclude_list = (
        'img_address',
    )

class MyModelViewCar(MyModelView):
    column_labels = dict(
        is_show=u'是否上架',
        full_name=u'名称',
        guid_price=u'指导价',
        price=u'出售价',
        deposit=u'订金',
        location=u'车源所在地',
        remark=u'备注',
    )
    column_searchable_list = (Car.full_name,)

# Flask views
@app.route('/')
def index():
    return render_template('index.html')

# Create admin
admin = flask_admin.Admin(
    app,
    u'链车后台系统',
    base_template='my_master.html',
    template_mode='bootstrap3',
)

# Add model views
#admin.add_view(MyModelView(Role, db.session))
admin.add_view(MyModelViewUser(User, db.session, name=u'用户'))
#admin.add_view(MyModelViewBrand(Brand, db.session,name=u'品牌', category=u'车辆'))
#admin.add_view(MyModelView(Category, db.session,name=u'车系', category=u'车辆'))
admin.add_view(MyModelViewCar(Car, db.session, name=u'车型'))

# define a context processor for merging flask-admin's template context into the
# flask-security views.
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )


