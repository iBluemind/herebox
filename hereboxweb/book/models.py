# -*- coding: utf-8 -*-


import datetime

from sqlalchemy import and_
from sqlalchemy.orm import relationship

from hereboxweb import database
from hereboxweb.utils import JsonSerializable


# 입고
class Incoming(database.Model, JsonSerializable):

    __tablename__ = 'incoming'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    goods_id = database.Column(database.Integer, database.ForeignKey('goods.id'), nullable=True)
    created_at = database.Column(database.DateTime)

    def __init__(self, goods_id):
        self.goods_id = goods_id
        self.created_at = datetime.datetime.now()


# 출고
class Outgoing(database.Model, JsonSerializable):

    __tablename__ = 'outgoing'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    goods_id = database.Column(database.Integer, database.ForeignKey('goods.id'), nullable=True)
    created_at = database.Column(database.DateTime)

    def __init__(self, goods_id):
        self.goods_id = goods_id
        self.created_at = datetime.datetime.now()


class InStoreStatus(object):
    IN_STORE = 0        # 보관중
    OUT_OF_STORE = 1    # 보관 중 아님


class BoxStatus(object):
    AVAILABLE = 0       # 사용가능
    UNAVAILABLE = 1     # 사용중


class Box(database.Model, JsonSerializable):

    __tablename__ = 'box'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    box_id = database.Column(database.String(5))
    in_store = database.Column(database.SmallInteger)   # 창고에 보관 여부
    status = database.Column(database.SmallInteger)     # 박스의 사용여부
    goods_id = database.Column(database.Integer, database.ForeignKey('goods.id'), nullable=True)
    created_at = database.Column(database.DateTime)

    def __init__(self, box_id, in_store, status, goods_id=None):
        self.box_id = box_id
        self.in_store = in_store
        self.status = status
        self.goods_id = goods_id
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()


class GoodsType(object):
    STANDARD_BOX = 'A'        # 규격박스
    NONSTANDARD_GOODS = 'B'   # 비규격 물품


class GoodsStatus(object):
    ACTIVE = 0              # 활성화
    EXPIRED = 1             # 만료


class Goods(database.Model, JsonSerializable):

    __tablename__ = 'goods'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    name = database.Column(database.String(20))
    goods_id = database.Column(database.String(11))
    goods_type = database.Column(database.SmallInteger)
    memo = database.Column(database.Text)
    photo = database.Column(database.Text)
    in_store = database.Column(database.SmallInteger)   # 창고에 보관 여부
    status = database.Column(database.SmallInteger)
    box_id = database.Column(database.Integer, database.ForeignKey('box.id'), nullable=True)
    user_id = database.Column(database.Integer, database.ForeignKey('user.uid'), nullable=False)
    fixed_rate = database.Column(database.SmallInteger)   # 자동결제 여부
    expired_at = database.Column(database.Date)
    created_at = database.Column(database.DateTime)
    updated_at = database.Column(database.DateTime)

    def __init__(self, goods_type, name, memo, in_store, status, user_id, fixed_rate,
                                expired_at=None, schedules=None, box_id=None):
        self.goods_id = self._generate_goods_id(goods_type)
        self.goods_type = goods_type
        self.name = name
        self.memo = memo
        self.in_store = in_store
        self.box_id = box_id
        self.status = status
        self.user_id = user_id
        self.fixed_rate = fixed_rate
        self.schedules = schedules
        self.expired_at = expired_at
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()

    def _get_today_goods_count(self):
        today = datetime.date.today()
        return Goods.query.filter(and_(Goods.created_at >= today.strftime('%Y-%m-%d 00:00:00'),
                                       Goods.created_at <= today.strftime('%Y-%m-%d 23:59:59'))).count()

    def _generate_goods_id(self, first_char):
        today = datetime.date.today()
        day_number = today.strftime('%y%m%d')
        init_number = 20
        serial_number = init_number + self._get_today_goods_count()
        return '%c%s00%s' % (first_char, day_number, serial_number)


