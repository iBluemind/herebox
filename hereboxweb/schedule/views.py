# -*- coding: utf-8 -*-
import base64
import re

from datetime import timedelta
from flask import request, render_template, redirect, url_for, make_response, session, escape
from flask.ext.login import login_required, current_user
from sqlalchemy import or_
from sqlalchemy.orm import aliased

from hereboxweb import database, response_template, bad_request
from hereboxweb.admin.models import VisitTime
from hereboxweb.auth.models import User
from hereboxweb.schedule import schedule
from hereboxweb.schedule.models import *


SCHEDULE_LIST_MAX_COUNT = 10


@schedule.route('/my_schedule', methods=['GET'])
@login_required
def my_schedule():
    staff = aliased(User, name="staff")
    customer = aliased(User, name="customer")

    my_pickup_schedules = database.session.query(
        Schedule,
        staff.name.label("staff_name"),
        customer.name.label("customer_name")).join((staff, Schedule.staff),
                                                  (customer, Schedule.customer)).filter(
        Schedule.customer_id == current_user.uid,
        or_(Schedule.schedule_type == ScheduleType.PICKUP_DELIVERY,
            Schedule.schedule_type == ScheduleType.PICKUP_RECOVERY)
    ).order_by(Schedule.updated_at.desc()).limit(SCHEDULE_LIST_MAX_COUNT).all()

    packed_my_pickup = []
    for item in my_pickup_schedules:
        packed_my_pickup.append(item[0])

    my_delivery_schedules = database.session.query(
        Schedule,
        staff.name.label("staff_name"),
        customer.name.label("customer_name")).join((staff, Schedule.staff),
                                                   (customer, Schedule.customer)).filter(
        Schedule.customer_id == current_user.uid,
        Schedule.schedule_type == ScheduleType.DELIVERY
    ).order_by(Schedule.updated_at.desc()).limit(SCHEDULE_LIST_MAX_COUNT).all()

    packed_my_delivery = []
    for item in my_delivery_schedules:
        packed_my_delivery.append(item[0])

    return render_template('my_schedule.html', active_my_index='my_schedule',
                           packed_my_pickup=packed_my_pickup,
                           packed_my_delivery=packed_my_delivery)


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


@schedule.route('/reservation/estimate', methods=['GET', 'POST'])
@login_required
def estimate():
    if request.method == 'POST':
        return save_order()

    estimate_info = get_estimate()
    if not estimate_info:
        return render_template('estimate.html', active_menu='reservation')

    response = make_response(render_template('estimate.html', active_menu='reservation',
                                             regular_item_count=estimate_info.get('regularItemNumberCount'),
                                             irregular_item_count=estimate_info.get('irregularItemNumberCount'),
                                             period=estimate_info.get('disposableNumberCount'),
                                             period_option=estimate_info.get('optionsPeriod'),
                                             binding_product0_count=estimate_info.get('bindingProduct0NumberCount'),
                                             binding_product1_count=estimate_info.get('bindingProduct1NumberCount'),
                                             binding_product2_count=estimate_info.get('bindingProduct2NumberCount'),
                                             binding_product3_count=estimate_info.get('bindingProduct3NumberCount'),
                                             promotion=estimate_info.get('inputPromotion'))
                             )

    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    response.headers.add('Last-Modified', datetime.datetime.now())
    response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')
    response.headers.add('Pragma', 'no-cache')
    return response


@schedule.route('/reservation/order', methods=['GET', 'POST'])
@login_required
def order():
    if request.method == 'POST':
        return save_estimate()

    try:
        estimate_info = get_estimate()
        estimate_info['startTime']
        estimate_info['regularItemNumberCount']
        estimate_info['irregularItemNumberCount']
        estimate_info['optionsPeriod']
        estimate_info['bindingProduct0NumberCount']
        estimate_info['bindingProduct1NumberCount']
        estimate_info['bindingProduct2NumberCount']
        estimate_info['bindingProduct3NumberCount']
    except:
        return redirect(url_for('schedule.estimate'))

    response = make_response(
        render_template('reservation.html', active_menu='reservation', old_phone_number=current_user.phone))

    order_info = get_order()
    if order_info:
        response = make_response(
            render_template('reservation.html', active_menu='reservation', old_phone_number=current_user.phone,
                                                address1=order_info.get('inputAddress1'),
                                                address2=order_info.get('inputAddress2'),
                                                user_memo=order_info.get('textareaMemo')))

    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    response.headers.add('Last-Modified', datetime.datetime.now())
    response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')
    response.headers.add('Pragma', 'no-cache')
    return response


@schedule.route('/reservation/review', methods=['GET', 'POST'])
@login_required
def review():
    if request.method == 'POST':
        return save_order()

    estimate_info = get_estimate()
    if not estimate_info:
        return redirect(url_for('schedule.estimate'))

    regular_item_count = estimate_info.get('regularItemNumberCount')
    irregular_item_count = estimate_info.get('irregularItemNumberCount')
    period = estimate_info.get('disposableNumberCount')
    period_option = estimate_info.get('optionsPeriod')
    binding_product0_count = estimate_info.get('bindingProduct0NumberCount')
    binding_product1_count = estimate_info.get('bindingProduct1NumberCount')
    binding_product2_count = estimate_info.get('bindingProduct2NumberCount')
    binding_product3_count = estimate_info.get('bindingProduct3NumberCount')
    promotion = estimate_info.get('inputPromotion')
    start_time = estimate_info.get('startTime')

    if not start_time:
        return redirect(url_for('schedule.estimate'))

    order_info = get_order()
    if not order_info:
        return redirect(url_for('schedule.estimate'))

    revisit_option = order_info.get('optionsRevisit')
    phone_number = order_info.get('inputPhoneNumber')
    revisit_time = order_info.get('inputRevisitTime')
    user_memo = order_info.get('textareaMemo')
    revisit_date = order_info.get('inputRevisitDate')
    visit_date = order_info.get('inputVisitDate')
    post_code = order_info.get('inputPostCode')
    address1 = order_info.get('inputAddress1')
    address2 = order_info.get('inputAddress2')
    visit_time = order_info.get('inputVisitTime')

    if not post_code:
        return redirect(url_for('schedule.estimate'))

    try:
        regular_item_count = int(regular_item_count)
        irregular_item_count = int(irregular_item_count)
        period = int(period)
        binding_product0_count = int(binding_product0_count)
        binding_product1_count = int(binding_product1_count)
        binding_product2_count = int(binding_product2_count)
        binding_product3_count = int(binding_product3_count)
    except:
        return redirect(url_for('schedule.estimate'))

    def calculate_total_price():
        total_storage_price = 0
        if period_option == 'subscription':
            # 매월 자동 결제일 경우!
            total_storage_price = total_storage_price + (7500 * regular_item_count)
            total_storage_price = total_storage_price + (9900 * irregular_item_count)
        else:
            total_storage_price = total_storage_price + (7500 * period * regular_item_count)
            total_storage_price = total_storage_price + (9900 * period * irregular_item_count)

        total_binding_products_price = 0
        total_binding_products_price = total_binding_products_price + 500 * binding_product0_count
        total_binding_products_price = total_binding_products_price + 500 * binding_product1_count
        total_binding_products_price = total_binding_products_price + 1500 * binding_product2_count
        total_binding_products_price = total_binding_products_price + 1000 * binding_product3_count

        return total_storage_price + total_binding_products_price

    visit_time = VisitTime.query.get(visit_time)
    if revisit_time:
        revisit_time = VisitTime.query.get(revisit_time)

    response = make_response(render_template('review.html', active_menu='reservation',
                                             standard_box_count=regular_item_count,
                                             nonstandard_goods_count=irregular_item_count,
                                             period_option=True if period_option == 'subscription' else False,
                                             period=period,
                                             binding_products={u'포장용 에어캡 1m': binding_product0_count,
                                                               u'실리카겔 (제습제) 50g': binding_product1_count,
                                                               u'압축팩 40cm x 60cm': binding_product2_count,
                                                               u'테이프 48mm x 40m': binding_product3_count},
                                             promotion=promotion,
                                             total_price=u'{:,d}원'.format(calculate_total_price()),
                                             phone=phone_number,
                                             address='%s %s' % (address1, address2),
                                             visit_date=visit_date,
                                             visit_time=visit_time,
                                             revisit_option=1 if revisit_option == 'later' else 0,
                                             revisit_date=revisit_date,
                                             revisit_time=revisit_time,
                                             user_memo=user_memo)
                                            )

    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    response.headers.add('Last-Modified', datetime.datetime.now())
    response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')
    response.headers.add('Pragma', 'no-cache')

    response.set_cookie('totalPrice', '%d' % (calculate_total_price()), path='/reservation/')
    return response


@schedule.route('/reservation/completion', methods=['GET'])
@login_required
def completion():
    return render_template('completion.html', active_menu='reservation')
