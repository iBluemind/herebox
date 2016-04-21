# -*- coding: utf-8 -*-
import re
import time

from datetime import timedelta
from flask import request, render_template, escape, session, redirect, url_for, make_response
from flask.ext.login import login_required, current_user
from hereboxweb import database, response_template, bad_request
from hereboxweb.auth.models import User
from hereboxweb.payment import payment
from hereboxweb.payment.models import *
from hereboxweb.schedule.models import Reservation, ReservationStatus, ReservationType, PurchaseType


@payment.route('/reservation/payment', methods=['GET', 'POST'])
@login_required
def reservation_payment():
    if request.method == 'POST':
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
        purchase_type = request.form.get('optionsPayType')

        try:
            regular_item_count = int(regular_item_count)
            binding_product0_count = int(binding_product0_count)
            binding_product1_count = int(binding_product1_count)
            binding_product2_count = int(binding_product2_count)
            binding_product3_count = int(binding_product3_count)
            period = int(period)
            irregular_item_count = int(irregular_item_count)
        except:
            return bad_request(u'잘못된 요청입니다.')

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

        print day_standard_time1.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        if converted_start_time > day_standard_time1 and converted_start_time <= day_standard_time2:
            converted_visit_date = datetime.datetime.strptime(visit_date, "%Y-%m-%d")
            converted_revisit_date = datetime.datetime.strptime(revisit_date, "%Y-%m-%d")
            today = datetime.datetime.now()
            tommorrow = today + timedelta(days=1)

            if converted_visit_date <= tommorrow or converted_revisit_date <= tommorrow:
                return bad_request(u'오후 5시가 넘어 내일을 방문예정일로 설정할 수 없습니다.')

        purchase_types = {
            'visit': PurchaseType.DIRECT,
            'card': PurchaseType.CARD,
            'phone': PurchaseType.PHONE,
            'kakao': PurchaseType.KAKAOPAY,
        }

        new_reservation = Reservation(
            reservation_type=ReservationType.PICKUP_NEW,
            status=ReservationStatus.WAITING,
            standard_box_count=regular_item_count,
            nonstandard_goods_count=irregular_item_count,
            period=period,
            fixed_rate=1 if period_option == 'subscription' else 0,
            promotion=promotion,
            binding_products={u'포장용 에어캡 1m': binding_product0_count, u'실리카겔 (제습제) 50g': binding_product1_count,
                              u'압축팩 40cm x 60cm': binding_product2_count, u'테이프 48mm x 40m': binding_product3_count},
            contact=phone_number,
            address='%s %s' % (address1, address2),
            delivery_date=visit_date,
            delivery_time=visit_time,
            recovery_date=revisit_date,
            recovery_time=revisit_time,
            revisit_option=1 if revisit_option == 'later' else 0,
            user_memo=user_memo,
            purchase_type=purchase_types[purchase_type],
            user_id=current_user.uid,
        )

        try:
            database.session.add(new_reservation)
            logged_in_user = User.query.get(current_user.uid)
            logged_in_user.phone = phone_number
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', 500)
        return response_template(u'정상 처리되었습니다', 200)

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
        request.cookies['totalPrice']
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
        request.cookies['startTime']
        request.cookies['inputVisitDate']
        request.cookies['inputPostCode']
        request.cookies['inputAddress1']
        request.cookies['inputAddress2']
        request.cookies['inputVisitTime']
    except:
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
        return bad_request(u'잘못된 요청입니다.')

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

    user_total_price = int(request.cookies.get('totalPrice'))
    total_price = calculate_total_price()

    if user_total_price != total_price:
        return redirect(url_for('schedule.estimate'))
    return render_template('reservation_payment.html', active_my_index='my_schedule')

