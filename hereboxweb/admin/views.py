# -*- coding: utf-8 -*-


import datetime
from flask import request, render_template
from hereboxweb import database, response_template
from hereboxweb.admin import admin
from hereboxweb.book.models import GoodsType, Box, Goods, InStoreStatus
from hereboxweb.schedule.models import Reservation, ReservationStatus, ScheduleType, ScheduleStatus
from hereboxweb.utils import add_months


@admin.route('/reservation/accept', methods=['POST'])
# @staff_required
def accept_reservation():
    reservation_id = request.form.get('reservation_id')
    reservation = Reservation.query.filter(Reservation.reservation_id == reservation_id).first()
    if not reservation:
        return response_template(u'%s 주문을 찾을 수 없습니다.' % reservation_id, status=400)

    reservation.status = ReservationStatus.ACCEPTED

    try:
        database.session.commit()
    except:
        return response_template(u'오류가 발생했습니다.', status=500)
    return response_template(u'정상 처리되었습니다.')


@admin.route('/goods/allocate', methods=['POST'])
# @staff_required
def allocate_goods():
    goods_type = request.form.get('goods_type')
    reservation_id = request.form.get('reservation_id')
    name = request.form.get('name')
    box_id = request.form.get('box_id')
    memo = request.form.get('memo')
    user_id = request.form.get('uid')

    box = None
    if goods_type == GoodsType.STANDARD_BOX:
        box = Box.query.filter(Box.box_id == box_id).first()
        if not box:
            return response_template(u'%s 상자를 찾을 수 없습니다.' % box_id, status=400)

    reservation = Reservation.query.filter(
                        Reservation.reservation_id == reservation_id,
                        Reservation.status == ReservationStatus.ACCEPTED).first()
    if not reservation:
        return response_template(u'접수된 주문 %s을 찾을 수 없습니다.' % reservation_id, status=400)

    schedules = reservation.schedules
    pickup_schedules = []
    for schedule in schedules:
        if schedule.schedule_type == ScheduleType.PICKUP_DELIVERY or\
                schedule.schedule_type == ScheduleType.PICKUP_RECOVERY:
            schedule.status = ScheduleStatus.COMPLETE
            pickup_schedules.append(schedule)

    today = datetime.date.today()
    expired = add_months(today, reservation.period)

    new_goods = Goods(goods_type=goods_type,
                      name=name,
                      memo=memo,
                      in_store=InStoreStatus.IN_STORE,
                      box_id=box.id if box else None,
                      user_id=user_id,
                      schedules=pickup_schedules,
                      expired_at=expired,
                      fixed_rate=reservation.fixed_rate)

    try:
        database.session.add(new_goods)
        database.session.commit()
    except:
        return response_template(u'오류가 발생했습니다.', status=500)
    return response_template(u'정상 처리되었습니다.')


@admin.route('/goods/store', methods=['POST'])
# @staff_required
def store_goods():
    goods_id = request.form.get('goods_id')

    goods = Goods.query.filter(Goods.goods_id == goods_id,
                                Goods.in_store == InStoreStatus.OUT_OF_STORE)\
                            .first()

    goods.in_store = InStoreStatus.IN_STORE

    try:
        database.session.commit()
    except:
        return response_template(u'오류가 발생했습니다.', status=500)
    return response_template(u'정상 처리되었습니다.')


@admin.route('/goods/release', methods=['POST'])
# @staff_required
def release_goods():
    goods_id = request.form.get('goods_id')

    goods = Goods.query.filter(Goods.goods_id == goods_id,
                                Goods.in_store == InStoreStatus.IN_STORE)\
                            .first()

    goods.in_store = InStoreStatus.OUT_OF_STORE

    try:
        database.session.commit()
    except:
        return response_template(u'오류가 발생했습니다.', status=500)
    return response_template(u'정상 처리되었습니다.')