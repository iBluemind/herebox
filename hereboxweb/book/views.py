# -*- coding: utf-8 -*-


import calendar
import json

from flask import request, render_template, make_response, redirect, url_for
from flask.ext.login import login_required, current_user
from hereboxweb import database, response_template
from hereboxweb.book.models import *
from hereboxweb.book import book
from hereboxweb.schedule.models import Reservation
from hereboxweb.utils import staff_required, add_months

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

    today = datetime.date.today()
    expired = add_months(today, reservation.period)

    new_goods = Goods(goods_type=goods_type,
                      name=name,
                      memo=memo,
                      in_store=InStoreStatus.IN_STORE,
                      box_id=box.id if box else None,
                      user_id=user_id,
                      reservations=[Reservation.query.get(reservation.id)],
                      expired_at=expired)

    try:
        database.session.add(new_goods)
        database.session.commit()
    except:
        return response_template(u'오류가 발생했습니다.', status=500)
    return response_template(u'정상 처리되었습니다.')


def save_stuffs():
    stuff_ids = request.form.get('stuffIds')
    if not stuff_ids:
        return response_template(u'물품 아이디가 없습니다.', status=400)

    stuff_ids = json.loads(stuff_ids)

    stuffs = Goods.query.filter(
        Goods.goods_id.in_(stuff_ids)
    ).limit(10).all()

    if not stuffs:
        return response_template(u'해당되는 물품이 없습니다.', status=400)

    stuff_info = {}
    for stuff in stuffs:
        stuff_info[str(stuff.goods_id)] = 0

    response = make_response(response_template(u'정상 처리되었습니다.'))
    response.set_cookie('estimate', json.dumps(stuff_info), path='/extended/')
    return response


def get_stuffs():
    stuffs = request.cookies.get('estimate')
    if stuffs:
        stuffs = json.loads(stuffs)
        stuffs = Goods.query.filter(
            Goods.goods_id.in_(stuffs.keys())
        ).limit(10).all()

        packed_stuffs = []
        for item in stuffs:
            today = datetime.date.today()
            remaining_day = item.expired_at - today
            item.remaining_day = remaining_day.days
            packed_stuffs.append(item)

        return packed_stuffs


@book.route('/extended/estimate', methods=['GET', 'POST'])
@login_required
def extended_estimate():
    if request.method == 'POST':
        return save_stuffs()

    packed_stuffs = get_stuffs()
    if not packed_stuffs:
        return redirect(url_for('book.my_stuff'))

    if len(packed_stuffs) == 0:
        return redirect(url_for('book.my_stuff'))

    return render_template('extended_estimate.html', active_menu='reservation',
                           packed_stuffs=packed_stuffs)


@book.route('/extended/review', methods=['GET', 'POST'])
@login_required
def extended_review():
    if request.method == 'POST':
        new_estimate_info = request.form.get('estimate')
        old_estimate_info = request.cookies.get('estimate')
        start_time = request.form.get('startTime')
        user_total_price = request.form.get('totalPrice')

        if not old_estimate_info or not new_estimate_info or not start_time\
                or not user_total_price:
            return response_template(u'잘못된 요청입니다.', status=400)

        old_estimate_info = json.loads(old_estimate_info)
        new_estimate_info = json.loads(new_estimate_info)

        total_price = 0
        for goods_id in old_estimate_info.keys():
            if type(new_estimate_info[goods_id]) is int:
                if goods_id.startswith('B'):
                    total_price += (9900 * new_estimate_info[goods_id])
                else:
                    total_price += (7500 * new_estimate_info[goods_id])
            else:
                del new_estimate_info[goods_id]

        response = make_response(response_template(u'정상 처리되었습니다.'))
        response.set_cookie('estimate', json.dumps(new_estimate_info), path='/extended/')

        try:
            datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            user_total_price = int(user_total_price)
        except:
            return response_template(u'잘못된 요청입니다.', status=400)

        if user_total_price != total_price:
            return response_template(u'잘못된 요청입니다.', status=400)

        order_info = {
            'start_time': start_time,
            'total_price': total_price
        }

        response.set_cookie('order', json.dumps(order_info), path='/extended/')
        return response

    estimate_info = request.cookies.get('estimate')
    order_info = request.cookies.get('order')
    if not estimate_info or not order_info:
        return redirect(url_for('book.my_stuff'))

    estimate_info = json.loads(estimate_info)
    order_info = json.loads(order_info)

    stuffs = Goods.query.filter(
        Goods.goods_id.in_(estimate_info.keys())
    ).limit(10).all()

    packed_stuffs = []
    for item in stuffs:
        item.new_period = estimate_info[item.goods_id]
        packed_stuffs.append(item)

    if len(packed_stuffs) == 0:
        return redirect(url_for('book.my_stuff'))

    return render_template('extended_review.html', active_menu='reservation',
                           packed_stuffs=packed_stuffs,
                           total_price=u'{:,d}원'.format(order_info['total_price']))


@book.route('/extended/completion', methods=['GET'])
@login_required
def extended_completion():
    return render_template('extended_completion.html', active_menu='reservation')

