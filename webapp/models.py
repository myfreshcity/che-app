from flask_security import RoleMixin, UserMixin

from webapp.app import db

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('roles.id')))


class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return '<Role %s>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(63))
    current_login_ip = db.Column(db.String(63))
    login_count = db.Column(db.Integer)
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users'))  # , lazy='dynamic'))


class Brand(db.Model):
    __tablename__ = 't_brand'
    id = db.Column(db.Integer(), primary_key=True)
    initial = db.Column(db.VARCHAR(50))
    full_name = db.Column(db.VARCHAR(255))
    img_address = db.Column(db.VARCHAR(255))

    def __repr__(self):
        return "<Brand %s>"%self.id


class Category(db.Model):
    __tablename__ = 'car_categorys'
    id = db.Column(db.Integer(), primary_key=True)
    full_name = db.Column(db.VARCHAR(255))
    img_url = db.Column(db.VARCHAR(255))

    def __repr__(self):
        return "<Category %s>" % self.id


class Car(db.Model):
    __tablename__ = 'cars'
    id = db.Column(db.Integer(), primary_key=True)
    full_name = db.Column(db.VARCHAR(255))
    guid_price = db.Column(db.VARCHAR(50))
    price = db.Column(db.VARCHAR(50))
    deposit = db.Column(db.Integer())
    location = db.Column(db.VARCHAR(50))
    is_show = db.Column(db.Boolean())
    remark = db.Column(db.VARCHAR(500))

    def __repr__(self):
        return "<Car %s>" % self.id


