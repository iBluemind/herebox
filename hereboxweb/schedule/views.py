# -*- coding: utf-8 -*-
import re

from datetime import timedelta
from flask import request, render_template, redirect, url_for, make_response, session, escape
from flask.ext.login import login_required, current_user

from hereboxweb import database, response_template, bad_request
from hereboxweb.admin.models import VisitTime
from hereboxweb.schedule import schedule
from hereboxweb.schedule.models import *
from hereboxweb.tasks import expire_draft_reservation


@schedule.route('/my_schedule', methods=['GET'])
@login_required
def my_schedule():
    return render_template('my_schedule.html', active_my_index='my_schedule')


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

    if regular_item_count != None:
        response.set_cookie('regularItemNumberCount', str(regular_item_count), path='/reservation/')
    if irregular_item_count != None:
        response.set_cookie('irregularItemNumberCount', str(irregular_item_count), path='/reservation/')
    if period != None:
        response.set_cookie('disposableNumberCount', str(period), path='/reservation/')
    if period_option != None:
        response.set_cookie('optionsPeriod', str(period_option), path='/reservation/')
    if binding_product0_count != None:
        response.set_cookie('bindingProduct0NumberCount', str(binding_product0_count), path='/reservation/')
    if binding_product1_count != None:
        response.set_cookie('bindingProduct1NumberCount', str(binding_product1_count), path='/reservation/')
    if binding_product2_count != None:
        response.set_cookie('bindingProduct2NumberCount', str(binding_product2_count), path='/reservation/')
    if binding_product3_count != None:
        response.set_cookie('bindingProduct3NumberCount', str(binding_product3_count), path='/reservation/')
    if promotion != None:
        response.set_cookie('inputPromotion', str(promotion), path='/reservation/')
    if start_time != None:
        response.set_cookie('startTime', str(start_time), path='/reservation/')
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
    start_time = request.cookies.get('startTime')

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

    if revisit_option != None:
        response.set_cookie('optionsRevisit', str(revisit_option), path='/reservation/')
    if phone_number != None:
        response.set_cookie('inputPhoneNumber', str(phone_number), path='/reservation/')
    if revisit_time != None:
        response.set_cookie('inputRevisitTime', str(revisit_time), path='/reservation/')
    if user_memo != None:
        response.set_cookie('textareaMemo', user_memo, path='/reservation/')
    if revisit_date != None:
        response.set_cookie('inputRevisitDate', str(revisit_date), path='/reservation/')
    if visit_date != None:
        response.set_cookie('inputVisitDate', str(visit_date), path='/reservation/')
    if post_code != None:
        response.set_cookie('inputPostCode', str(post_code), path='/reservation/')
    if address1 != None:
        response.set_cookie('inputAddress1', address1, path='/reservation/')
    if address2 != None:
        response.set_cookie('inputAddress2', address2, path='/reservation/')
    if visit_time != None:
        response.set_cookie('inputVisitTime', str(visit_time), path='/reservation/')
    return response


@schedule.route('/reservation/estimate', methods=['GET', 'POST'])
@login_required
def estimate():
    if request.method == 'POST':
        return save_order()

    regular_item_count = request.cookies.get('regularItemNumberCount')
    irregular_item_count = request.cookies.get('irregularItemNumberCount')
    period = request.cookies.get('disposableNumberCount')
    period_option = request.cookies.get('optionsPeriod')
    binding_product0_count = request.cookies.get('bindingProduct0NumberCount')
    binding_product1_count = request.cookies.get('bindingProduct1NumberCount')
    binding_product2_count = request.cookies.get('bindingProduct2NumberCount')
    binding_product3_count = request.cookies.get('bindingProduct3NumberCount')
    promotion = request.cookies.get('inputPromotion')

    response = make_response(render_template('estimate.html', active_menu='reservation',
                                             regular_item_count=regular_item_count,
                                             irregular_item_count=irregular_item_count,
                                             period=period,
                                             period_option=period_option,
                                             binding_product0_count=binding_product0_count,
                                             binding_product1_count=binding_product1_count,
                                             binding_product2_count=binding_product2_count,
                                             binding_product3_count=binding_product3_count,
                                             promotion=promotion)
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
        request.cookies['startTime']
        request.cookies['regularItemNumberCount']
        request.cookies['irregularItemNumberCount']
        request.cookies['disposableNumberCount']
        request.cookies['optionsPeriod']
        request.cookies['bindingProduct0NumberCount']
        request.cookies['bindingProduct1NumberCount']
        request.cookies['bindingProduct2NumberCount']
        request.cookies['bindingProduct3NumberCount']
    except:
        return redirect(url_for('schedule.estimate'))

    revisit_option = request.cookies.get('optionsRevisit')
    phone_number = request.cookies.get('inputPhoneNumber')
    revisit_time = request.cookies.get('inputRevisitTime')
    user_memo = request.cookies.get('textareaMemo')
    start_time = request.cookies.get('startTime')
    revisit_date = request.cookies.get('inputRevisitDate')
    visit_date = request.cookies.get('inputVisitDate')
    post_code = request.cookies.get('inputPostCode')
    address1 = request.cookies.get('inputAddress1')
    address2 = request.cookies.get('inputAddress2')
    visit_time = request.cookies.get('inputVisitTime')

    response = make_response(
        render_template('reservation.html', active_menu='reservation', old_phone_number=current_user.phone,
                        revisit_option=revisit_option,
                        phone_number=phone_number,
                        revisit_time=revisit_time,
                        user_memo=user_memo,
                        start_time=start_time,
                        revisit_date=revisit_date,
                        visit_date=visit_date,
                        post_code=post_code,
                        address1=address1,
                        address2=address2,
                        visit_time=visit_time)
        )
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

    try:
        request.cookies['regularItemNumberCount']
        request.cookies['irregularItemNumberCount']
        request.cookies['disposableNumberCount']
        request.cookies['optionsPeriod']
        request.cookies['bindingProduct0NumberCount']
        request.cookies['bindingProduct1NumberCount']
        request.cookies['bindingProduct2NumberCount']
        request.cookies['bindingProduct3NumberCount']
        request.cookies['optionsRevisit']
        request.cookies['inputPhoneNumber']
        request.cookies['inputRevisitTime']
        request.cookies['startTime']
        request.cookies['inputVisitDate']
        request.cookies['inputPostCode']
        request.cookies['inputAddress1']
        request.cookies['inputAddress2']
    except:
        return redirect(url_for('schedule.estimate'))

    regular_item_count = request.cookies.get('regularItemNumberCount')
    irregular_item_count = request.cookies.get('irregularItemNumberCount')
    period = request.cookies.get('disposableNumberCount')
    period_option = request.cookies.get('optionsPeriod')
    binding_product0_count = request.cookies.get('bindingProduct0NumberCount')
    binding_product1_count = request.cookies.get('bindingProduct1NumberCount')
    binding_product2_count = request.cookies.get('bindingProduct2NumberCount')
    binding_product3_count = request.cookies.get('bindingProduct3NumberCount')
    promotion = request.cookies.get('inputPromotion')
    revisit_option = request.cookies.get('optionsRevisit')
    phone_number = request.cookies.get('inputPhoneNumber')
    revisit_time = request.cookies.get('inputRevisitTime')
    user_memo = request.cookies.get('textareaMemo')
    start_time = request.cookies.get('startTime')
    revisit_date = request.cookies.get('inputRevisitDate')
    visit_date = request.cookies.get('inputVisitDate')
    post_code = request.cookies.get('inputPostCode')
    address1 = request.cookies.get('inputAddress1')
    address2 = request.cookies.get('inputAddress2')
    visit_time = request.cookies.get('inputVisitTime')

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
