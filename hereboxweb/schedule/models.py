# -*- coding: utf-8 -*-


import datetime
import json

import sqlalchemy
from sqlalchemy import and_
from sqlalchemy.orm import relationship

from hereboxweb import database
from hereboxweb.auth.models import User
from hereboxweb.utils import JsonSerializable


# 예약 타입
class ReservationType(object):
    PICKUP_NEW = 'N'    # 신규픽업
    PICKUP_AGAIN = 'R'  # 재보관
    DELIVERY = 'D'      # 배송

    table_name_map = {
        PICKUP_NEW: 'new_reservation',
        PICKUP_AGAIN: 'restore_reservation',
        DELIVERY: 'delivery_reservation',
    }


# 예약 상태
class ReservationStatus(object):
    WAITING = 0     # 대기
    ACCEPTED = 1    # 접수


class ReservationRevisitType(object):
    IMMEDIATE = 0               # 즉시 가능
    LATER = 1                   # 재방문 신청


class ReservationDeliveryType(object):
    RESTORE = 0         # 재보관 가능
    EXPIRE = 1          # 보관 종료


class ReservationUtils(object):
    def _get_today_reservation_count(self, cls):
        today = datetime.date.today()
        return cls.query.filter(and_(cls.created_at >= today.strftime('%Y-%m-%d 00:00:00'),
                                     cls.created_at <= today.strftime(
                                                    '%Y-%m-%d 23:59:59'))).count()

    def _generate_reservation_id(self, first_char, cls):
        today = datetime.date.today()
        day_number = today.strftime('%y%m%d')
        init_number = 20
        serial_number = init_number + self._get_today_reservation_count(cls)
        return '%c%s00%s' % (first_char, day_number, serial_number)


reservation_goods = database.Table(
                        'reservation_goods',
                            database.Column('reservation', database.Integer, database.ForeignKey('reservation.id')),
                            database.Column('goods', database.Integer, database.ForeignKey('goods.id'))
                    )


class Reservation(database.Model, JsonSerializable, ReservationUtils):

    __tablename__ = 'reservation'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    reservation_id = database.Column(database.String(11), unique=True)
    reservation_type = database.Column(database.String(30))                         # 예약 종류
    status = database.Column(database.SmallInteger)                                 # 예약 접수 상태
    pay_type = database.Column(database.SmallInteger)                               # 결제 방법
    contact = database.Column(database.Text)                                        # 연락처
    address = database.Column(database.Text)                                        # 방문주소
    delivery_date = database.Column(database.Date)                                  # 방문일시(배달)
    delivery_time = database.Column(database.Integer,
                                    database.ForeignKey('visit_time.id'), nullable=True)
    user_memo = database.Column(database.Text)                                      # 남기실말씀
    purchase_id = database.Column(database.Integer,
                                  database.ForeignKey('purchase.id'), nullable=True)
    user_id = database.Column(database.Integer,
                              database.ForeignKey('user.uid'), nullable=False)
    created_at = database.Column(database.DateTime)
    updated_at = database.Column(database.DateTime)
    schedules = database.relationship('Schedule', backref='reservation', lazy='dynamic')
    goods = database.relationship('Goods', secondary=reservation_goods,
                           backref=database.backref('reservations', lazy='dynamic'))

    __mapper_args__ = {
        'polymorphic_on': reservation_type,
        'polymorphic_identity': 'reservation',
        'with_polymorphic': '*'
    }


# 배달 예약
class DeliveryReservation(Reservation):

    __tablename__ = 'delivery_reservation'

    id = database.Column(database.Integer, database.ForeignKey('reservation.id'), primary_key=True)
    delivery_option = database.Column(database.SmallInteger)

    __mapper_args__ = {'polymorphic_identity': 'delivery_reservation'}

    def __init__(self, status, user_id, contact, address, delivery_option,
                 delivery_date, delivery_time, user_memo,
                 pay_type, purchase_id=None, goods=None):
        self.reservation_type = ReservationType.table_name_map[ReservationType.DELIVERY]
        self.reservation_id = self._generate_reservation_id(ReservationType.DELIVERY, DeliveryReservation)
        self.status = status
        self.pay_type = pay_type
        self.contact = contact
        self.address = address
        self.delivery_option = delivery_option
        self.delivery_date = delivery_date
        self.delivery_time = delivery_time
        self.user_memo = user_memo
        self.purchase_id = purchase_id
        self.user_id = user_id
        self.goods = goods
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()


# 재보관 예약
class RestoreReservation(Reservation):

    __tablename__ = 'restore_reservation'

    id = database.Column(database.Integer, database.ForeignKey('reservation.id'), primary_key=True)
    recovery_date = database.Column(database.Date)                                      # 방문일시(회수)
    recovery_time = database.Column(database.Integer,
                                    database.ForeignKey('visit_time.id'), nullable=True)
    revisit_option = database.Column(database.SmallInteger)                             # 재방문 여부(배달날짜 != 회수날짜)

    __mapper_args__ = {'polymorphic_identity': 'restore_reservation'}

    def __init__(self, status, user_id, contact, address,
                 delivery_date, delivery_time, recovery_date,
                 recovery_time, revisit_option, user_memo,
                 pay_type, purchase_id=None, goods=None):
        self.reservation_type = ReservationType.table_name_map[ReservationType.PICKUP_AGAIN]
        self.reservation_id = self._generate_reservation_id(ReservationType.PICKUP_AGAIN, RestoreReservation)
        self.status = status
        self.pay_type = pay_type
        self.contact = contact
        self.address = address
        self.delivery_date = delivery_date
        self.delivery_time = delivery_time
        self.recovery_date = recovery_date
        self.recovery_time = recovery_time
        self.revisit_option = revisit_option
        self.user_memo = user_memo
        self.purchase_id = purchase_id
        self.user_id = user_id
        self.goods = goods
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()



# 신규 예약
class NewReservation(Reservation):

    __tablename__ = 'new_reservation'

    id = database.Column(database.Integer, database.ForeignKey('reservation.id'), primary_key=True)
    standard_box_count = database.Column(database.SmallInteger)                 # 규격박스 갯수
    nonstandard_goods_count = database.Column(database.SmallInteger)            # 비규격물품 갯수
    period = database.Column(database.SmallInteger)                             # 계약 월수
    fixed_rate = database.Column(database.SmallInteger)                         # 자동결제 여부
    promotion = database.Column(database.Text)                                  # 프로모션 코드
    binding_products = database.Column(database.Text)                           # 포장용품
    recovery_date = database.Column(database.Date)                              # 방문일시(회수)
    recovery_time = database.Column(database.Integer,
                                    database.ForeignKey('visit_time.id'), nullable=True)
    revisit_option = database.Column(database.SmallInteger)                     # 재방문 여부(배달날짜 != 회수날짜)
    promotion_id = database.Column(database.Integer,
                                   database.ForeignKey('promotion.id'), nullable=True)

    __mapper_args__ = {'polymorphic_identity': 'new_reservation'}

    def __init__(self, status, standard_box_count, nonstandard_goods_count,
                                    period, fixed_rate, binding_products, user_id, promotion, contact,
                                    address, delivery_date, delivery_time, recovery_date,
                                    recovery_time, revisit_option, user_memo,
                                    pay_type, purchase_id=None, goods=None, promotion_id=None):
        self.reservation_type = ReservationType.table_name_map[ReservationType.PICKUP_NEW]
        self.reservation_id = self._generate_reservation_id(ReservationType.PICKUP_NEW, NewReservation)
        self.status = status
        self.standard_box_count = standard_box_count
        self.nonstandard_goods_count = nonstandard_goods_count
        self.period = period
        self.pay_type = pay_type
        self.fixed_rate = fixed_rate
        self.promotion = promotion
        self.binding_products = self.parse_binding_products(binding_products)
        self.contact = contact
        self.address = address
        self.delivery_date = delivery_date
        self.delivery_time = delivery_time
        self.recovery_date = recovery_date
        self.recovery_time = recovery_time
        self.revisit_option = revisit_option
        self.user_memo = user_memo
        self.purchase_id = purchase_id
        self.user_id = user_id
        self.promotion_id = promotion_id
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()

    def parse_binding_products(self, binding_products):
        return json.dumps(binding_products)



class ScheduleType(object):
    PICKUP_DELIVERY = 0     # 배달(픽업)
    PICKUP_RECOVERY = 1     # 회수(픽업)
    DELIVERY = 2            # 배송
    RESTORE_DELIVERY = 3    # 배달(재보관)
    RESTORE_RECOVERY = 4    # 회수(재보관)


class ScheduleStatus(object):
    WAITING = 0         # 대기
    COMPLETE = 1        # 완료
    CANCELED = 2        # 취소


# 스케줄
class Schedule(database.Model, JsonSerializable):

    __tablename__ = 'schedule'
    __table_args__ = (
        sqlalchemy.ForeignKeyConstraint(['staff_id'], ['user.uid']),
        sqlalchemy.ForeignKeyConstraint(['customer_id'], ['user.uid']),
        sqlalchemy.ForeignKeyConstraint(['reservation_id'], ['reservation.id']),
        sqlalchemy.ForeignKeyConstraint(['schedule_time_id'], ['visit_time.id']),
    )

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    status = database.Column(database.SmallInteger)
    schedule_type = database.Column(database.SmallInteger)
    staff_id = database.Column(database.Integer, database.ForeignKey('user.uid'), nullable=True)
    customer_id = database.Column(database.Integer, database.ForeignKey('user.uid'), nullable=False)
    goods_id = database.Column(database.Integer, database.ForeignKey('goods.id'), nullable=True)
    schedule_date = database.Column(database.Date)
    schedule_time_id = database.Column(database.Integer, database.ForeignKey('visit_time.id'), nullable=False)
    reservation_id = database.Column(database.Integer,
                                     database.ForeignKey('reservation.id'), nullable=True)
    schedule_id = database.Column(database.String(13), unique=True)
    created_at = database.Column(database.DateTime)
    updated_at = database.Column(database.DateTime)
    staff = relationship(User,
                        primaryjoin="Schedule.staff_id==User.uid",
                        foreign_keys=User.uid)
    customer = relationship(User,
                            primaryjoin="Schedule.customer_id==User.uid",
                            foreign_keys=User.uid)

    def __init__(self, status, schedule_type, customer_id, schedule_date, schedule_time_id,
                                            reservation_id=None, staff_id=None, goods_id=None):
        self.status = status
        self.schedule_type = schedule_type
        self.staff_id = staff_id
        self.customer_id = customer_id
        self.schedule_date = schedule_date
        self.schedule_time_id = schedule_time_id
        self.reservation_id = reservation_id
        self.schedule_id = self._generate_schedule_id(schedule_type, reservation_id)
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()

    def _generate_schedule_id(self, schedule_type, reservation_id):
        reservation = Reservation.query.get(reservation_id)
        postfix = ''
        if (schedule_type == ScheduleType.PICKUP_DELIVERY) or\
                            (schedule_type == ScheduleType.RESTORE_DELIVERY):
            postfix = '_0'
        elif (schedule_type == ScheduleType.PICKUP_RECOVERY) or \
                (schedule_type == ScheduleType.RESTORE_RECOVERY):
            postfix = '_1'
        return '%s%s' % (reservation.reservation_id, postfix)


class PromotionType(object):
    ALLOW_TO_ALL = 0                # 모두에게 허용
    USER_SPECIFIC = 1               # 특정인에게만 허용


class Promotion(database.Model, JsonSerializable):

    __tablename__ = 'promotion'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    name = database.Column(database.String(15))
    description = database.Column(database.Text)
    promotion_type = database.Column(database.SmallInteger)
    codes = database.relationship('PromotionCode', backref='promotion', lazy='dynamic')
    expired_at = database.Column(database.DateTime)
    created_at = database.Column(database.DateTime)

    def __init__(self, name, description, promotion_type, expired_at):
        self.name = name
        self.description = description
        self.promotion_type = promotion_type
        self.expired_at = expired_at
        self.created_at = datetime.datetime.now()


class PromotionCode(database.Model, JsonSerializable):

    __tablename__ = 'promotion_code'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    code = database.Column(database.String(20))
    promotion_id = database.Column(database.Integer, database.ForeignKey('promotion.id'), nullable=False)
    created_at = database.Column(database.DateTime)
    histories = database.relationship('PromotionHistory', backref='promotion_code', lazy='dynamic')

    def __init__(self, code, promotion_id):
        self.code = code
        self.promotion_id = promotion_id
        self.created_at = datetime.datetime.now()


class PromotionHistory(database.Model, JsonSerializable):

    __tablename__ = 'promotion_history'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    user_id = database.Column(database.Integer, database.ForeignKey('user.uid'), nullable=False)
    code = database.Column(database.Integer, database.ForeignKey('promotion_code.id'), nullable=False)
    created_at = database.Column(database.DateTime)

    def __init__(self, user_id, code):
        self.user_id = user_id
        self.code = code
        self.created_at = datetime.datetime.now()


class ExtendPeriodStatus(object):
    WAITING = 0
    ACCEPTED = 1


class ExtendPeriod(database.Model):

    __tablename__ = 'extend_period'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    amount = database.Column(database.Integer, nullable=False)
    goods_id = database.Column(database.Integer, database.ForeignKey('goods.id'), nullable=False)
    status = database.Column(database.SmallInteger, default=ExtendPeriodStatus.WAITING)
    created_at = database.Column(database.DateTime)

    def __init__(self, amount, goods_id, status):
        self.amount = amount
        self.goods_id = goods_id
        self.status = status
        self.created_at = datetime.datetime.now()

