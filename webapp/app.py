import flask_admin
from flask import Flask, url_for, redirect, render_template, request, abort, jsonify
from flask_admin import helpers as admin_helpers
from flask_admin.contrib import sqla
from flask_babelex import Babel
from flask_security import Security, SQLAlchemyUserDatastore, \
    current_user, logout_user, login_user

# Create Flask application
from flask_security.utils import verify_password, hash_password

from config import config
from webapp import db
from webapp.services import get_brands, get_car_detail, get_index

app = Flask(__name__)
app.config.from_object(config)

db.init_app(app)

babel = Babel(app)
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'

from webapp.models import Role, User, Car

# Define models

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# Create customized model view class
class MyModelView(sqla.ModelView):
    can_delete = False

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
    can_create = False
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
        price=u'定金',
        offset_price=u'降价',
        location=u'车源所在地',
        remark=u'备注',
    )
    column_searchable_list = (Car.full_name,)

    column_exclude_list = (
        'brand','cat'
    )

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

# Flask views
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/index',methods=['POST','GET'])
def home_index():
    return jsonify(get_index())

@app.route('/api/category',methods=['POST','GET'])
def brands():
    return jsonify(get_brands())

@app.route('/api/detail',methods=['POST','GET'])
def car_detail():
    id = request.json['cid']
    return jsonify(get_car_detail(int(id)))

@app.route('/api/login', methods=['POST', 'GET'])
def login():
    if not current_user.is_anonymous:
        logout_user()
    username = request.json['username']
    password = request.json['password']

    user = User.query.filter_by(email=username).first()
    if user is None:
        return jsonify({'status': 500, 'message': '无效的用户名'})
    if not verify_password(password, user.password):
        return jsonify({'status': 500, 'message': '无效的密码'})
    login_user(user, remember=True)
    return jsonify({'status': 200, 'message': ''})

@app.route('/api/logout',methods=['POST','GET'])
def logout():
    logout_user()
    return jsonify({'status': 200, 'message': ''})

@app.route('/api/register', methods=['GET', 'POST'])
def register():
    username = request.json['username']
    password = request.json['password']

    user = User.query.filter_by(email=username).first()
    if user:
        return jsonify({'status': 500, 'message': '用户名已存在'})
    new_user = user_datastore.create_user(email=username, password=hash_password(password))
    normal_role = user_datastore.find_role('user')
    db.session.add(new_user)
    db.session.commit()
    user_datastore.add_role_to_user(new_user, normal_role)
    login_user(new_user)
    return jsonify({'status': 200, 'message': ''})




