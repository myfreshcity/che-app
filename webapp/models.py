from flask import current_app
from flask_security import RoleMixin, UserMixin
from sqlalchemy import func

from webapp import db

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

orders_cars = db.Table('orders_cars',
                       db.Column('order_id', db.Integer(), db.ForeignKey('orders.id')),
                       db.Column('car_id', db.Integer(), db.ForeignKey('cars.id')))


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    open_id = db.Column(db.String(50))

    pay_amt = db.Column(db.Integer())
    t_status = db.Column(db.Integer())
    pay_confirm_time = db.Column(db.DateTime)

    pay_person_type = db.Column(db.Integer())
    contact_way = db.Column(db.String(255))
    contact_person = db.Column(db.String(255))
    remark = db.Column(db.String(255))
    created_time = db.Column(db.DateTime, server_default=func.now())

    cars = db.relationship('Car', secondary=orders_cars,
                            backref=db.backref('orders'))  # , lazy='dynamic'))

    def to_json(self):
        obj = {
            'id': self.id,
            'pay_amt': self.pay_amt,
            't_status': self.t_status,
            'pay_person_type': self.pay_person_type,
            'contact_way': self.contact_way,
            'contact_person': self.contact_person,
            'remark': self.remark,
        }
        return obj

    def __repr__(self):
        return '<Order %s>' % self.id



class Brand(db.Model):
    __tablename__ = 'car_brands'
    id = db.Column(db.Integer(), primary_key=True)
    initial = db.Column(db.VARCHAR(50))
    full_name = db.Column(db.VARCHAR(255))
    img_address = db.Column(db.VARCHAR(255))

    def to_json(self):
        json_user = {
            'id': self.id,
            'full_name': self.full_name,
        }
        return json_user

    def __repr__(self):
        return "%s" % self.full_name


class Category(db.Model):
    __tablename__ = 'car_categorys'
    id = db.Column(db.Integer(), primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('car_brands.id'))
    full_name = db.Column(db.VARCHAR(255))
    img_url = db.Column(db.VARCHAR(255))

    def to_json(self):
        json_user = {
            'id': self.id,
            'full_name': self.full_name,
            'img_url': '%s/%s' % (current_app.config['IMG_PATH'],self.img_url),
        }
        return json_user

    def __repr__(self):
        return "%s" % self.full_name


class Car(db.Model):
    __tablename__ = 'cars'
    id = db.Column(db.Integer(), primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('car_brands.id'))
    cat_id = db.Column(db.Integer, db.ForeignKey('car_categorys.id'))

    full_name = db.Column(db.VARCHAR(255))
    guid_price = db.Column(db.VARCHAR(50))
    price = db.Column(db.VARCHAR(50))
    offset_price = db.Column(db.Integer())
    location = db.Column(db.VARCHAR(50))
    is_show = db.Column(db.Boolean())
    remark = db.Column(db.VARCHAR(500))

    brand = db.relationship("Brand")
    cat = db.relationship("Category")

    def to_json(self):
        json_user = {
            'id': self.id,
            'title': self.full_name,
            'guid_price': self.guid_price,
            'offset_price':self.offset_price,
            'price': self.price,
            'location': self.location,
            'is_show': self.is_show,
            'remark': self.remark,
            'img_url': '%s/%s' % (current_app.config['IMG_PATH'],self.cat.img_url)
            #'mp_count': self.subscribed_mps.count()
        }
        return json_user

    def __repr__(self):
        return "<Car %s>" % self.id


