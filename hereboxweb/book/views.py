# -*- coding: utf-8 -*-


import calendar
import json

from flask import request, render_template, make_response, redirect, url_for
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
                      reservations=[Reservation.query.get(reservation.id)],
                      expired_at=expired)

    try:
        database.session.add(new_goods)
        database.session.commit()
    except:
        return response_template(u'오류가 발생했습니다.', status=500)
    return response_template(u'정상 처리되었습니다.')


def get_estimate():
    estimate = request.cookies.get('estimate')
    if estimate:
        parsed_estimate = json.loads(estimate)
        return parsed_estimate


def get_order():
    order = request.cookies.get('order')
    if order:
        parsed_order = json.loads(order)
        return parsed_order


def save_estimate():
    regular_item_count = request.form.get('regularItemNumberCount')
    irregular_item_count = request.form.get('irregularItemNumberCount')
    period = request.form.get('disposableNumberCount')
    period_option = request.form.get('optionsPeriod')
    binding_product0_count = request.form.get('bindingProduct0NumberCount')
    binding_product1_count = request.form.get('bindingProduct1NumberCount')
    binding_product2_count = request.form.get('bindingProduct2NumberCount')
    binding_product3_count = request.form.get('bindingProduct3NumberCount')
    promotion = request.form.get('inputPromotion')
    start_time = request.form.get('startTime')

    try:
        regular_item_count = int(regular_item_count)
        irregular_item_count = int(irregular_item_count)
        period = int(period)
        binding_product0_count = int(binding_product0_count)
        binding_product1_count = int(binding_product1_count)
        binding_product2_count = int(binding_product2_count)
        binding_product3_count = int(binding_product3_count)
    except:
        return bad_request(u'잘못된 요청입니다.')

    response = make_response(render_template('reservation.html', active_menu='reservation',
                                             phone_number=current_user.phone))

    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    response.headers.add('Last-Modified', datetime.datetime.now())
    response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')
    response.headers.add('Pragma', 'no-cache')

    estimate_info = {
        'regularItemNumberCount': regular_item_count,
        'irregularItemNumberCount': irregular_item_count,
        'optionsPeriod': period_option,
        'bindingProduct0NumberCount': binding_product0_count,
        'bindingProduct1NumberCount': binding_product1_count,
        'bindingProduct2NumberCount': binding_product2_count,
        'bindingProduct3NumberCount': binding_product3_count,
        'startTime': start_time,
    }

    if period != None:
        estimate_info['disposableNumberCount'] = period
    if promotion != None:
        estimate_info['inputPromotion'] = promotion

    response.set_cookie('estimate', json.dumps(estimate_info), path='/reservation/')
    return response


def save_order():
    revisit_option = request.form.get('optionsRevisit')
    phone_number = request.form.get('inputPhoneNumber')
    revisit_time = request.form.get('inputRevisitTime')
    user_memo = request.form.get('textareaMemo')
    revisit_date = request.form.get('inputRevisitDate')
    visit_date = request.form.get('inputVisitDate')
    post_code = request.form.get('inputPostCode')
    address1 = request.form.get('inputAddress1')
    address2 = request.form.get('inputAddress2')
    visit_time = request.form.get('inputVisitTime')

    if not re.match('^([0]{1}[1]{1}[016789]{1})([0-9]{3,4})([0-9]{4})$', phone_number):
        return bad_request(u'잘못된 전화번호입니다.')

    if len(user_memo) > 200:
        return bad_request(u'메모가 너무 깁니다.')

    if len(address1) > 200:
        return bad_request(u'address1이 너무 깁니다.')

    if len(address2) > 200:
        return bad_request(u'address2가 너무 깁니다.')

    if current_user.phone:
        if current_user.phone != phone_number:
            return bad_request(u'연락처 정보가 다릅니다.')

    if revisit_option == 'immediate':
        revisit_date = visit_date
        revisit_time = visit_time

    estimate = get_estimate()
    start_time = estimate['startTime']

    converted_start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    day_standard_time1 = converted_start_time.replace(hour=17, minute=0)  # 저녁 5시 기준
    day_standard_time2 = converted_start_time.replace(hour=23, minute=59, second=59)

    if converted_start_time > day_standard_time1 and converted_start_time <= day_standard_time2:
        converted_visit_date = datetime.datetime.strptime(visit_date, "%Y-%m-%d")
        converted_revisit_date = datetime.datetime.strptime(revisit_date, "%Y-%m-%d")
        today = datetime.datetime.now()
        tommorrow = today + timedelta(days=1)

        if converted_visit_date <= tommorrow or converted_revisit_date <= tommorrow:
            return bad_request(u'오후 5시가 넘어 내일을 방문예정일로 설정할 수 없습니다.')

    response = make_response(render_template('reservation.html', active_menu='reservation',
                                             phone_number=current_user.phone))

    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    response.headers.add('Last-Modified', datetime.datetime.now())
    response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')
    response.headers.add('Pragma', 'no-cache')

    order_info = {
        'optionsRevisit': revisit_option,
        'inputPhoneNumber': phone_number,
        'inputVisitDate': visit_date,
        'inputPostCode': post_code,
        'inputVisitTime': visit_time,
        'inputAddress1': address1,
        'inputAddress2': address2,
    }

    if revisit_time != None:
        order_info['inputRevisitTime'] = revisit_time
    if revisit_date != None:
        order_info['inputRevisitDate'] = revisit_date
    if user_memo != None:
        order_info['textareaMemo'] = user_memo
    response.set_cookie('order', json.dumps(order_info), path='/reservation/')
    return response


@book.route('/extended/estimate', methods=['GET', 'POST'])
@login_required
def extended_estimate():
    if request.method == 'POST':
        stuff_ids = request.form.get('stuffIds')
        if not stuff_ids:
            return response_template(u'물품 아이디가 없습니다.', status=400)

        stuff_ids = json.loads(stuff_ids)

        stuffs = Goods.query.filter(
            Goods.id.in_(stuff_ids)
        ).limit(10).all()

        if not stuffs:
            return response_template(u'해당되는 물품이 없습니다.', status=201)

        stuff_info = {}
        for stuff in stuffs:
            stuff_info[str(stuff.goods_id)] = 0

        response = make_response(response_template(u'정상 처리되었습니다.'))
        response.set_cookie('estimate', json.dumps(stuff_info), path='/extended/')
        return response

    stuffs = request.cookies.get('estimate')
    if not stuffs:
        return redirect(url_for('book.my_stuff'))

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

        print user_total_price
        print total_price

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
    stuffs = Goods.query.filter(
        Goods.goods_id.in_(estimate_info.keys())
    ).limit(10).all()

    order_info = json.loads(order_info)

    packed_stuffs = []
    for item in stuffs:
        item.new_period = estimate_info[item.goods_id]
        packed_stuffs.append(item)

    return render_template('extended_review.html', active_menu='reservation',
                           packed_stuffs=packed_stuffs,
                           total_price=u'{:,d}원'.format(order_info['total_price']))


@book.route('/extended/completion', methods=['GET'])
@login_required
def extended_completion():
    return render_template('extended_completion.html', active_menu='reservation')

