# -*- coding: utf-8 -*-


import datetime
from hereboxweb import database
from hereboxweb.utils import JsonSerializable


class PurchaseStatus(object):
    NORMAL = 0
    ERROR = 1


# 결제 방법
class PayType(object):
    CARD = 0
    DIRECT = 1
    PHONE = 2
    KAKAOPAY = 3
    ACCOUNT = 4     # 무통장입금



# 결제 내역
class Purchase(database.Model, JsonSerializable):

    __tablename__ = 'purchase'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    status = database.Column(database.SmallInteger)
    amount = database.Column(database.String(10))
    pay_type = database.Column(database.SmallInteger)
    user_id = database.Column(database.Integer, database.ForeignKey('user.uid'), nullable=False)
    created_at = database.Column(database.DateTime)
    reservations = database.relationship('Reservation', backref='purchase', lazy='dynamic')

    def __init__(self, status, amount, pay_type, user_id):
        self.status = status
        self.amount = amount
        self.pay_type = pay_type
        self.user_id = user_id
        self.created_at = datetime.datetime.now()

