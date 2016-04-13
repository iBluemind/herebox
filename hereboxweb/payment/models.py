# -*- coding: utf-8 -*-


import datetime
from hereboxweb import database
from hereboxweb.utils import JsonSerializable


class PurchaseStatus(object):
    NORMAL = 0
    ERROR = 1


# 결제 내역
class Purchase(database.Model, JsonSerializable):

    __tablename__ = 'purchase'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    status = database.Column(database.SmallInteger)
    amount = database.Column(database.String(10))
    user_id = database.Column(database.Integer, database.ForeignKey('user.uid'), nullable=False)
    created_at = database.Column(database.DateTime)

    def __init__(self, status, user_id, created_at):
        self.user_id = user_id
        self.status = status
        self.created_at = datetime.datetime.utcnow()

