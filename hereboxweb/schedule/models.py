# -*- coding: utf-8 -*-


import datetime
from hereboxweb import database
from hereboxweb.utils import JsonSerializable


# 예약 타입
class ReservationType(object):
    PICKUP_NEW = 'N'    # 신규픽업
    PICKUP_AGAIN = 'R'  # 재보관
    DELIVERY = 'D'      # 배송


# 예약 상태
class ReservationStatus(object):
    WAITING = 0     # 대기
    ACCEPTED = 1    # 접수


# 결제 방법
class PurchaseType(object):
    ONLINE = 0
    DIRECT = 1


# 예약
class Reservation(database.Model, JsonSerializable):

    __tablename__ = 'reservation'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    reservation_id = database.Column(database.String(11), unique=True)
    reservation_type = database.Column(database.String(1))                   # 예약 종류
    status = database.Column(database.SmallInteger)                     # 예약 접수 상태
    standard_box_count = database.Column(database.SmallInteger)         # 규격박스 갯수
    nonstandard_goods_count = database.Column(database.SmallInteger)    # 비규격물품 갯수
    period = database.Column(database.SmallInteger)                     # 계약 월수
    expire_date = database.Column(database.DateTime)                    # 계약 만료날짜
    purchase_type = database.Column(database.SmallInteger)              # 결제 방법
    fixed_rate = database.Column(database.SmallInteger)                 # 자동결제 여부
    promotion = database.Column(database.SmallInteger)                  # 프로모션 여부
    binding_products = database.Column(database.Text)                 # 포장용품
    contact = database.Column(database.Text)                          # 연락처
    address = database.Column(database.Text)                          # 방문주소
    delivery_date = database.Column(database.DateTime)                  # 방문일시(배달)
    recovery_date = database.Column(database.DateTime)                  # 방문일시(회수)
    user_memo = database.Column(database.Text)                        # 남기실말씀
    purchase_id = database.Column(database.Integer,
                                  database.ForeignKey('purchase.id'), nullable=True)
    user_id = database.Column(database.Integer,
                              database.ForeignKey('user.uid'), nullable=False)
    created_at = database.Column(database.DateTime)
    updated_at = database.Column(database.DateTime)

    def __init__(self, reservation_type, status, standard_box_count, nonstandard_goods_count,
                                    period, expire_date, purchase_type, fixed_rate,
                                    promotion, binding_products, contact, address, delivery_date,
                                    recovery_date, user_memo, purchase_id, user_id):
        self.reservation_id = self._generate_reservation_id(reservation_type)
        self.reservation_type = reservation_type
        self.status = status
        self.standard_box_count = standard_box_count
        self.nonstandard_goods_count = nonstandard_goods_count
        self.period = period
        self.expire_date = expire_date
        self.purchase_type = purchase_type
        self.fixed_rate = fixed_rate
        self.promotion = promotion
        self.binding_products = binding_products
        self.contact = contact
        self.address = address
        self.delivery_date = delivery_date
        self.recovery_date = recovery_date
        self.user_memo = user_memo
        self.purchase_id = purchase_id
        self.user_id = user_id
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()

    def _generate_reservation_id(self, first_char):
        today = datetime.date.today()
        day_number = today.strftime('%y%m%d')
        init_number = self._get_reservation_init_number()[first_char]
        serial_number = init_number + self.id
        return '%c%s00%s' % (first_char, day_number, serial_number)

    def _get_reservation_init_number(self):
        return {
            ReservationType.PICKUP_NEW: 20,
            ReservationType.PICKUP_AGAIN: 21,
            ReservationType.DELIVERY: 22
        }


class ScheduleType(object):
    PICKUP_DELIVERY = 0     # 배달(픽업)
    PICKUP_RECOVERY = 1     # 회수(픽업)
    DELIVERY = 2            # 배송


class ScheduleStatus(object):
    WAITING = 0         # 대기
    COMPLETE = 1        # 완료
    CANCELED = 2        # 취소


# 스케줄
class Schedule(database.Model, JsonSerializable):

    __tablename__ = 'schedule'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    status = database.Column(database.SmallInteger)
    staff_id = database.Column(database.Integer, database.ForeignKey('user.uid'), nullable=False)
    customer_id = database.Column(database.Integer, database.ForeignKey('user.uid'), nullable=False)
    goods_id = database.Column(database.Integer, database.ForeignKey('goods.id'), nullable=False)
    schedule_date = database.Column(database.DateTime)
    reservation_id = database.Column(database.Integer,
                                     database.ForeignKey('reservation.id'), nullable=True)
    created_at = database.Column(database.DateTime)
    updated_at = database.Column(database.DateTime)

    def __init__(self, status, staff_id, customer_id, schedule_date, reservation_id):
        self.status = status
        self.staff_id = staff_id
        self.customer_id = customer_id
        self.schedule_date = schedule_date
        self.reservation_id = reservation_id
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()


class CompletedSchedule(database.Model, JsonSerializable):

    __tablename__ = 'completed_schedule'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    purchase_id = database.Column(database.Integer,
                                  database.ForeignKey('purchase.id'), nullable=True)
    staff_id = database.Column(database.Integer, database.ForeignKey('user.uid'), nullable=False)
    customer_id = database.Column(database.Integer, database.ForeignKey('user.uid'), nullable=False)
    goods_id = database.Column(database.Integer, database.ForeignKey('goods.id'), nullable=False)
    reservation_id = database.Column(database.Integer,
                                     database.ForeignKey('reservation.id'), nullable=True)
    scheduled_at = database.Column(database.DateTime)       # 예약된 시간
    created_at = database.Column(database.DateTime)         # 완료된 시간

    def __init__(self, purchase_id, staff_id, customer_id, goods_id, reservation_id, scheduled_at):
        self.purchase_id = purchase_id
        self.staff_id = staff_id
        self.customer_id = customer_id
        self.goods_id = goods_id
        self.reservation_id = reservation_id
        self.scheduled_at = scheduled_at
        self.created_at = datetime.datetime.utcnow()


class CanceledSchedule(database.Model, JsonSerializable):

    __tablename__ = 'canceled_schedule'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    purchase_id = database.Column(database.Integer,
                                  database.ForeignKey('purchase.id'), nullable=True)
    staff_id = database.Column(database.Integer, database.ForeignKey('user.uid'), nullable=False)
    customer_id = database.Column(database.Integer, database.ForeignKey('user.uid'), nullable=False)
    goods_id = database.Column(database.Integer, database.ForeignKey('goods.id'), nullable=False)
    reason = database.Column(database.Text)
    reservation_id = database.Column(database.Integer,
                                     database.ForeignKey('reservation.id'), nullable=True)
    scheduled_at = database.Column(database.DateTime)   # 예약된 시간
    created_at = database.Column(database.DateTime)     # 취소된 시간

    def __init__(self, purchase_id, staff_id, customer_id, goods_id, reason, reservation_id, scheduled_at):
        self.purchase_id = purchase_id
        self.staff_id = staff_id
        self.customer_id = customer_id
        self.goods_id = goods_id
        self.reason = reason
        self.reservation_id = reservation_id
        self.scheduled_at = scheduled_at
        self.created_at = datetime.datetime.utcnow()

