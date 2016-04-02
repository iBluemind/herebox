# -*- coding: utf-8 -*-


import datetime
from flask import request, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from hereboxweb import database, response_template
from hereboxweb.utils import to_json


class User(database.Model):
    __tablename__ = 'user'

    uid = database.Column(database.Integer, primary_key=True, autoincrement=True)
    phone = database.Column(database.String(20), unique=True, nullable=False)
    name = database.Column(database.String(20), nullable=False)
    email = database.Column(database.String(30), unique=True, nullable=False)
    password = database.Column(database.Text, nullable=False)
    privilege = database.Column(database.SmallInteger, nullable=False)
    created_at = database.Column(database.DateTime)
    reservations = database.relationship('Reservation', backref='user', lazy='dynamic')
    purchases = database.relationship('Purchase', backref='user', lazy='dynamic')
    shopping_cart_items = database.relationship('ShoppingCart', backref='user', lazy='dynamic')
    alerts = database.relationship('Alert', backref='user', lazy='dynamic')

    def __init__(self, phone, email, name, privilege, password=None, school_id=None, gcm_id=None):
        self.phone = phone
        self.password = self.encrypt_password(password) if password != None else ''
        self.name = name
        self.email = email
        self.privilege = privilege
        self.school_id = school_id
        self.gcm_id = gcm_id
        self.created_at = datetime.datetime.utcnow()

    @staticmethod
    def encrypt_password(password):
        return generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @property
    def json(self):
        return to_json(self, self.__class__)