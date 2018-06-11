class Config():
    # Create dummy secrey key so we can use sessions
    SECRET_KEY = '123456790'

    # Create in-memory database
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@127.0.0.1:3306/car_shop?charset=utf8'
    SQLALCHEMY_ECHO = True

    # Flask-Security config
    SECURITY_URL_PREFIX = "/admin"
    SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
    SECURITY_PASSWORD_SALT = "ATGUOHAELKiubahiughaerGOJAEGj"

    # Flask-Security URLs, overridden because they don't put a / at the end
    SECURITY_LOGIN_URL = "/login/"
    SECURITY_LOGOUT_URL = "/logout/"
    SECURITY_REGISTER_URL = "/register/"

    SECURITY_POST_LOGIN_VIEW = "/admin/"
    SECURITY_POST_LOGOUT_VIEW = "/admin/"
    SECURITY_POST_REGISTER_VIEW = "/admin/"

    # Flask-Security features
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    IMG_PATH = 'https://carshop.manmanh.com/imgs'

    # weixin config

    APP_ID = 'wx286dca7ab8e2b933'  # 小程序ID
    APP_KEY = '9e0e06a06469d0fe9b6fc185724aadf1'  # 小程序ID
    MCH_ID = '1481660592'  # 商户号
    SPBILL_CREATE_IP = '111.111.111.11'  # 终端IP
    NOTIFY_URL = 'https://carshop.manmanh.com/api/wxpay/notify'  # 通知地址
    TRADE_TYPE = 'JSAPI'  # 交易类型
    MERCHANT_KEY = '87c7653ef2e2669488d4c766a212b205'  # 商户KEY

config = Config()