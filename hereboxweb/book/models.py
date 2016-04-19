# -*- coding: utf-8 -*-


import datetime
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


class InStoreStatusType(object):
    IN_STORE = 0        # 보관중
    OUT_OF_STORE = 1    # 보관 중 아님


class BoxStatusType(object):
    AVAILABLE = 0       # 사용가능
    UNAVAILABLE = 1     # 사용중


class Box(database.Model, JsonSerializable):

    __tablename__ = 'box'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    box_id = database.Column(database.String(5))
    in_store = database.Column(database.SmallInteger)   # 창고에 보관 여부
    status = database.Column(database.SmallInteger)     # 박스의 사용여부
    expired_at = database.Column(database.DateTime)
    created_at = database.Column(database.DateTime)

    def __init__(self, box_id, in_store, status, expired_at):
        self.box_id = box_id
        self.in_store = in_store
        self.status = status
        self.expired_at = expired_at
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()


class GoodsType(object):
    STANDARD_BOX = 'A'        # 규격박스
    NONSTANDARD_GOODS = 'B'   # 비규격 물품


class Goods(database.Model, JsonSerializable):

    __tablename__ = 'goods'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    goods_id = database.Column(database.String(11))
    goods_type = database.Column(database.SmallInteger)
    memo = database.Column(database.Text)
    in_store = database.Column(database.SmallInteger)   # 창고에 보관 여부
    box_id = database.Column(database.Integer, database.ForeignKey('box.id'), nullable=True)
    user_id = database.Column(database.Integer, database.ForeignKey('user.uid'), nullable=False)
    expired_at = database.Column(database.DateTime)
    created_at = database.Column(database.DateTime)
    updated_at = database.Column(database.DateTime)

    def __init__(self, goods_type, memo, in_store, box_id, user_id, expired_at):
        self.goods_id = self._generate_goods_id(goods_type)
        self.goods_type = goods_type
        self.memo = memo
        self.in_store = in_store
        self.box_id = box_id
        self.user_id = user_id
        self.expired_at = expired_at
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()

    def _generate_goods_id(self, first_char):
        today = datetime.date.today()
        day_number = today.strftime('%y%m%d')
        init_number = self._get_goods_init_number()[first_char]
        serial_number = init_number + self.id
        return '%c%s00%s' % (first_char, day_number, serial_number)

    def _get_goods_init_number(self):
        return {
            GoodsType.STANDARD_BOX: 20,
            GoodsType.NONSTANDARD_GOODS: 21,
        }

