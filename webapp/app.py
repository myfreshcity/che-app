import datetime

import flask_admin
from flask import Flask, url_for, render_template, request, abort, jsonify, current_app, make_response, \
    session
from flask_admin import helpers as admin_helpers
from flask_babelex import Babel
from flask_security import Security, SQLAlchemyUserDatastore, \
    current_user, logout_user, login_user
# Create Flask application
from flask_security.utils import verify_password, hash_password

from config import config
from webapp import db
from webapp.model_views import MyModelViewUser, MyModelViewCar, MyModelViewOrder
from webapp.services import get_brands, get_car_detail, get_index, get_openid, create_order
from webapp.wxpay import get_nonce_str, WxPay, xml_to_dict, dict_to_xml

app = Flask(__name__)
app.config.from_object(config)

db.init_app(app)

babel = Babel(app)
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'

from webapp.models import Role, User, Car, Order

# Define models

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# Create customized model view class

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
admin.add_view(MyModelViewOrder(Order, db.session, name=u'订单'))

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
    try:
        openid = request.json['oid']
        session['openid'] = openid
    except Exception:
        app.logger.error('user weixin login fail...')

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
    openid = session['openid']

    user = User.query.filter_by(email=username).first()
    if user:
        return jsonify({'status': 500, 'message': '用户名已存在'})

    user = User.query.filter_by(openid=openid).first()
    if user:
        return jsonify({'status': 500, 'message': '该账号在微信已注册'})

    new_user = user_datastore.create_user(email=username, password=hash_password(password))
    normal_role = user_datastore.find_role('user')
    new_user.openid = openid
    db.session.add(new_user)
    db.session.commit()
    user_datastore.add_role_to_user(new_user, normal_role)
    login_user(new_user)
    return jsonify({'status': 200, 'message': ''})


@app.route('/api/wx/openid/<code>')
def get_wx_openid(code):
    result = get_openid(code)
    if result:
        resp = make_response(jsonify({'status': 200, 'message': '', 'result': result}))
        resp.headers['openid'] = result['openid']
        session['openid'] = result['openid']
        return resp
    else:
        return abort(500)

@app.route('/api/orders', methods=['GET'])
def orders():
    if not current_user.is_anonymous:
        openid = current_user.openid
    else:
        return abort(403)

    orders = Order.query.filter_by(open_id=openid).all()
    result = []
    for od in orders:
        result.append(od.to_json())
    return jsonify({'status': 200, 'message': '', 'result': result})

@app.route('/api/wxpay/prepay', methods=['POST'])
def init_pay():
    pay_form = request.json['pay_form']
    car_list = request.json['car_list']
    total_fee = int(request.json['total_fee'])
    order = create_order(pay_form,car_list,total_fee)
    if order:
        return jsonify({'status': 200, 'message': '', 'result': order.to_json()})
    else:
        return abort(500)

@app.route('/api/wxpay/pay', methods=['POST'])
def create_pay():
    '''
    请求支付
    :return:
    '''
    order_id = request.json['order_id']
    openid = request.json['openid']

    order = db.session.query(Order).filter(Order.id == order_id).first()
    order.open_id = openid
    order.t_status = 10
    if current_app.config['TEST_ENV']:
        total_fee = 1
    else:
        total_fee = order.pay_amt*100
        order.pay_amt = total_fee


    data = {
        'appid': current_app.config['APP_ID'],
        'mch_id': current_app.config['MCH_ID'],
        'nonce_str': get_nonce_str(),
        'body': '商品描述',                              # 商品描述
        'out_trade_no': str(order.id),       # 商户订单号
        'total_fee': total_fee,
        'spbill_create_ip': current_app.config['SPBILL_CREATE_IP'],
        'notify_url': current_app.config['NOTIFY_URL'],
        'attach': '{"msg": "自定义数据"}',
        'trade_type': current_app.config['TRADE_TYPE'],
        'openid': openid
    }

    wxpay = WxPay(current_app.config['MERCHANT_KEY'], **data)
    pay_info = wxpay.get_pay_info()
    if pay_info:
        db.session.commit()
        return jsonify({'status': 200, 'message': '','result':pay_info})
    return jsonify({'status': 500, 'message': '请求支付失败'})


@app.route('/api/wxpay/notify', methods=['POST'])
def wxpay():
    '''
    支付回调通知
    :return:
    '''
    if request.method == 'POST':
        req_data = xml_to_dict(request.data)
        order = db.session.query(Order).filter(Order.id == req_data['out_trade_no']).first()
        order.t_status = 20
        order.pay_confirm_time = datetime.datetime.now()
        db.session.commit()

        result_data = {
            'return_code': 'SUCCESS',
            'return_msg': 'OK'
        }
        return dict_to_xml(result_data), {'Content-Type': 'application/xml'}

