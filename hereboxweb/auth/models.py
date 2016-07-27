# -*- coding: utf-8 -*-


import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hereboxweb import database, login_manager
from hereboxweb.utils import JsonSerializable


class UserStatus(object):
    DEACTIVATED = 0     # 비활성화(탈퇴)
    NORMAL = 1          # 일반회원
    STAFF = 2           # 직원
    ADMIN = 3           # 슈퍼유저



class User(database.Model, UserMixin, JsonSerializable):

    __tablename__ = 'user'

    uid = database.Column(database.Integer, primary_key=True, autoincrement=True)
    phone = database.Column(database.String(20), nullable=True)
    name = database.Column(database.String(20), nullable=False)
    email = database.Column(database.String(30), unique=True, nullable=True)
    password = database.Column(database.Text, nullable=False)
    address1 = database.Column(database.String(200), nullable=True)
    address2 = database.Column(database.String(200), nullable=True)
    status = database.Column(database.SmallInteger, nullable=False)
    created_at = database.Column(database.DateTime)
    fb_user_id = database.Column(database.String(100), nullable=True)
    fb_access_token = database.Column(database.String(200), nullable=True)
    goods = database.relationship('Goods', backref='user', lazy='dynamic')
    reservations = database.relationship('Reservation', backref='user', lazy='dynamic')
    purchases = database.relationship('Purchase', backref='user', lazy='dynamic')

    def __init__(self, name, email=None, fb_user_id=None, fb_access_token=None,
                        address1=None, address2=None, status=UserStatus.NORMAL, password=None, phone=None):
        self.phone = phone
        self.password = self.encrypt_password(password) if password != None else ''
        self.name = name
        self.email = email
        self.status = status
        self.address1 = address1
        self.address2 = address2
        self.fb_user_id = fb_user_id
        self.fb_access_token = fb_access_token
        self.created_at = datetime.datetime.now()

    @staticmethod
    def encrypt_password(password):
        return generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_id(self):
        return self.email or self.fb_user_id

    @property
    def is_active(self):
        return True if self.status > UserStatus.DEACTIVATED else False


@login_manager.user_loader
def load_user(user_id):
    login_user = database.session.query(User).filter(User.email == user_id).first()
    if not login_user:
        login_user = database.session.query(User).filter(User.fb_user_id == user_id).first()
    return login_user

