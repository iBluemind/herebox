# -*- coding: utf-8 -*-


import calendar
from flask import request, render_template
from flask.ext.login import login_required, current_user
from hereboxweb import database, response_template
from hereboxweb.book.models import *
from hereboxweb.book import book
from hereboxweb.schedule.models import Reservation
from hereboxweb.utils import staff_required


STUFF_LIST_MAX_COUNT = 10


@book.route('/my_stuff', methods=['GET'])
@login_required
def my_stuff():

    my_herebox_stuffs = Goods.query.filter(
        Goods.user_id == current_user.uid,
        Goods.in_store == InStoreStatus.IN_STORE
    ).order_by(Goods.created_at.desc()).limit(STUFF_LIST_MAX_COUNT).all()

    packed_my_herebox_stuffs = []
    for item in my_herebox_stuffs:
        today = datetime.date.today()
        remaining_day = item.expired_at - today
        item.remaining_day = remaining_day.days
        packed_my_herebox_stuffs.append(item)

    my_stuffs = Goods.query.filter(
        Goods.user_id == current_user.uid,
        Goods.in_store == InStoreStatus.OUT_OF_STORE
    ).order_by(Goods.created_at.desc()).limit(STUFF_LIST_MAX_COUNT).all()

    packed_my_stuffs = []
    for item in my_stuffs:
        packed_my_stuffs.append(item)

    return render_template('my_stuff.html', active_my_index='my_stuff',
                           packed_my_herebox_stuffs=packed_my_herebox_stuffs,
                           packed_my_stuffs=packed_my_stuffs)


@book.route('/goods', methods=['POST'])
# @staff_required
def goods():
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

    reservation = Reservation.query.filter(Reservation.reservation_id == reservation_id).first()
    if not reservation:
        return response_template(u'%s 주문을 찾을 수 없습니다.' % reservation_id, status=400)

    def add_months(src_date, months):
        month = src_date.month - 1 + months
        year = int(src_date.year + month / 12)
        month = month % 12 + 1
        day = min(src_date.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day)

    today = datetime.date.today()
    expired = add_months(today, reservation.period)

    new_goods = Goods(goods_type=goods_type,
                      name=name,
                      memo=memo,
                      in_store=InStoreStatus.IN_STORE,
                      box_id=box.id if box else None,
                      user_id=user_id,
                      reservation_id=reservation.id,
                      expired_at=expired)

    try:
        database.session.add(new_goods)
        database.session.commit()
    except:
        return response_template(u'오류가 발생했습니다.', status=500)
    return response_template(u'정상 처리되었습니다.')

