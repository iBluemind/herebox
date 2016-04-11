# -*- coding: utf-8 -*-
import datetime
from flask import request, render_template
from hereboxweb import database, response_template
from hereboxweb.utils import to_json


# 예약 타입
class ReservationType(object):
    DELIVERY = 0    # 배달
    RECOVERY = 1    # 회수


# 예약 상태
class ReservationStatus(object):
    WAITING = 0     # 대기
    COMPLETE = 1    # 완료


# 예약
class Reservation(database.Model):

    __tablename__ = 'reservation'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    type = database.Column(database.SmallInteger)
    status = database.Column(database.SmallInteger)
    user_id = database.Column(database.Integer, database.ForeignKey('user.uid'), nullable=False)
    created_at = database.Column(database.DateTime)

    def __init__(self, type, status, user_id):
        self.type = type
        self.user_id = user_id
        self.status = status
        self.created_at = datetime.datetime.utcnow()

    @property
    def json(self):
        return to_json(self, self.__class__)


# 스케줄
class Schedule(database.Model):

    __tablename__ = 'schedule'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)


    created_at = database.Column(database.DateTime)

    def __init__(self, book_id, user_id, status, receipt_date, school_id):
        self.book_id = book_id
        self.user_id = user_id
        self.status = status
        self.receipt_date = receipt_date
        self.school_id = school_id
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()

    @property
    def json(self):
        return to_json(self, self.__class__)


# 이력
class History(database.Model):

    __tablename__ = 'history'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)

    created_at = database.Column(database.DateTime)

    def __init__(self, book_id, user_id, status, receipt_date, school_id):
        self.book_id = book_id
        self.user_id = user_id
        self.status = status
        self.receipt_date = receipt_date
        self.school_id = school_id
        self.created_at = datetime.datetime.utcnow()

    @property
    def json(self):
        return to_json(self, self.__class__)


# 입고
class Incoming(database.Model):

    __tablename__ = 'incoming'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)

    created_at = database.Column(database.DateTime)

    def __init__(self, book_id, user_id, status, receipt_date, school_id):
        self.book_id = book_id
        self.user_id = user_id
        self.status = status
        self.receipt_date = receipt_date
        self.school_id = school_id
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()

    @property
    def json(self):
        return to_json(self, self.__class__)


# 출고
class Outgoing(database.Model):

    __tablename__ = 'outgoing'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)

    created_at = database.Column(database.DateTime)

    def __init__(self, book_id, user_id, status, receipt_date, school_id):
        self.book_id = book_id
        self.user_id = user_id
        self.status = status
        self.receipt_date = receipt_date
        self.school_id = school_id
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()

    @property
    def json(self):
        return to_json(self, self.__class__)


class Box(database.Model):

    __tablename__ = 'box'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)

    created_at = database.Column(database.DateTime)

    def __init__(self, book_id, user_id, status, receipt_date, school_id):
        self.book_id = book_id
        self.user_id = user_id
        self.status = status
        self.receipt_date = receipt_date
        self.school_id = school_id
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()

    @property
    def json(self):
        return to_json(self, self.__class__)


class Warehouse(database.Model):

    __tablename__ = 'warehouse'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)

    created_at = database.Column(database.DateTime)

    def __init__(self, book_id, user_id, status, receipt_date, school_id):
        self.book_id = book_id
        self.user_id = user_id
        self.status = status
        self.receipt_date = receipt_date
        self.school_id = school_id
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()

    @property
    def json(self):
        return to_json(self, self.__class__)

