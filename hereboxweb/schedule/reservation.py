# -*- coding: utf-8 -*-

import json
import datetime
import re
from flask import request, make_response, render_template, escape, session
from flask.ext.login import current_user
from hereboxweb import bad_request


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

    try:
        regular_item_count = int(regular_item_count)
        irregular_item_count = int(irregular_item_count)
        if period_option == 'disposable':
            period = int(period)
        binding_product0_count = int(binding_product0_count)
        binding_product1_count = int(binding_product1_count)
        binding_product2_count = int(binding_product2_count)
        binding_product3_count = int(binding_product3_count)
    except:
        return bad_request(u'잘못된 요청입니다.')

    response = make_response(render_template('reservation.html', active_menu='reservation',
                                             phone_number=current_user.phone))

    estimate_info = {
        'regularItemNumberCount': regular_item_count,
        'irregularItemNumberCount': irregular_item_count,
        'optionsPeriod': period_option,
        'bindingProduct0NumberCount': binding_product0_count,
        'bindingProduct1NumberCount': binding_product1_count,
        'bindingProduct2NumberCount': binding_product2_count,
        'bindingProduct3NumberCount': binding_product3_count,
    }

    if period_option == 'disposable':
        estimate_info['disposableNumberCount'] = period
    if promotion != None:
        estimate_info['inputPromotion'] = promotion

    response.set_cookie('estimate', json.dumps(estimate_info), path='/reservation/')
    return response


def save_order(template, api_endpoint):
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

    start_time = escape(session.get('start_time'))
    converted_start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    day_standard_time1 = converted_start_time.replace(hour=17, minute=0)  # 저녁 5시 기준
    day_standard_time2 = converted_start_time.replace(hour=23, minute=59, second=59)

    if converted_start_time > day_standard_time1 and converted_start_time <= day_standard_time2:
        converted_visit_date = datetime.datetime.strptime(visit_date, "%Y-%m-%d")
        converted_revisit_date = datetime.datetime.strptime(revisit_date, "%Y-%m-%d")
        today = datetime.datetime.now()
        tommorrow = today + datetime.timedelta(days=1)

        if converted_visit_date <= tommorrow or converted_revisit_date <= tommorrow:
            return bad_request(u'오후 5시가 넘어 내일을 방문예정일로 설정할 수 없습니다.')

    response = make_response(render_template(template, active_menu='reservation',
                                             phone_number=current_user.phone))

    order_info = {
        'optionsRevisit': revisit_option,
        'inputPhoneNumber': phone_number,
        'inputVisitDate': visit_date,
        'inputPostCode': post_code,
        'inputVisitTime': visit_time,
        'inputAddress1': address1,
        'inputAddress2': address2,
    }

    if revisit_option == 'later':
        order_info['inputRevisitTime'] = revisit_time
        order_info['inputRevisitDate'] = revisit_date
    if user_memo != None:
        order_info['textareaMemo'] = user_memo
    response.set_cookie('order', json.dumps(order_info), path=api_endpoint)
    return response


def apply_hellohb_promotion(regular_item_count, irregular_item_count, period):
    total_storage_price = 0
    discount_count = 10
    discount_count = discount_count - irregular_item_count
    if discount_count >= 0:
        total_storage_price = total_storage_price + (9900 * irregular_item_count * (period - 1))
    else:
        total_storage_price = total_storage_price + (9900 * 10 * (period - 1))
        total_storage_price = total_storage_price + (9900 * (discount_count * -1) * period)

    if discount_count > 0:
        if regular_item_count > 0:
            discount_count = discount_count - regular_item_count
            if discount_count >= 0:
                total_storage_price = total_storage_price + (7500 * regular_item_count * (period - 1))
            else:
                total_storage_price = total_storage_price + (7500 * 10 * (period - 1))
                total_storage_price = total_storage_price + (7500 * (discount_count * -1) * period)
    else:
        total_storage_price = total_storage_price + (7500 * regular_item_count * period)

    return total_storage_price


def calculate_storage_price(regular_item_count, irregular_item_count, period_option, period, promotion=None):
    total_storage_price = 0
    if period_option == 'subscription':
        # 매월 자동 결제일 경우!
        total_storage_price = total_storage_price + (7500 * regular_item_count)
        total_storage_price = total_storage_price + (9900 * irregular_item_count)
    else:
        if 'HELLOHB' == promotion:
            total_storage_price = apply_hellohb_promotion(regular_item_count, irregular_item_count, period)
        else:
            total_storage_price = total_storage_price + (7500 * period * regular_item_count)
            total_storage_price = total_storage_price + (9900 * period * irregular_item_count)
    return total_storage_price


def calculate_binding_products_price(binding_product0_count, binding_product1_count, binding_product2_count,
                                        binding_product3_count):
    total_binding_products_price = 0
    total_binding_products_price = total_binding_products_price + 500 * binding_product0_count
    total_binding_products_price = total_binding_products_price + 500 * binding_product1_count
    total_binding_products_price = total_binding_products_price + 1500 * binding_product2_count
    total_binding_products_price = total_binding_products_price + 1000 * binding_product3_count
    return total_binding_products_price


def calculate_total_price(regular_item_count, irregular_item_count, period, period_option, promotion,
                          binding_product0_count, binding_product1_count, binding_product2_count,
                          binding_product3_count):
    total_storage_price = calculate_storage_price(regular_item_count, irregular_item_count,
                                                  period_option,
                                                  period, promotion)

    total_binding_products_price = calculate_binding_products_price(binding_product0_count,
                                                                        binding_product1_count,
                                                                        binding_product2_count,
                                                                        binding_product3_count)

    return total_storage_price + total_binding_products_price