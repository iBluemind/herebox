# -*- coding: utf-8 -*-
import json
import re
import time

from datetime import timedelta
from flask import request, render_template, escape, session, redirect, url_for, make_response
from flask.ext.login import login_required, current_user
from hereboxweb import database, response_template, bad_request
from hereboxweb.admin.models import VisitTime
from hereboxweb.auth.models import User
from hereboxweb.book.models import Goods
from hereboxweb.book.views import get_stuffs
from hereboxweb.payment import payment
from hereboxweb.payment.models import *
from hereboxweb.schedule.models import NewReservation, ReservationStatus, ReservationType, Schedule, \
    ScheduleStatus, ScheduleType, ReservationRevisitType, DeliveryReservation, RestoreReservation
from hereboxweb.schedule.views import get_order, get_estimate
from hereboxweb.utils import add_months

pay_types = {
    'visit': PayType.DIRECT,
    'card': PayType.CARD,
    'phone': PayType.PHONE,
    'kakao': PayType.KAKAOPAY,
}


@payment.route('/pickup/payment', methods=['GET', 'POST'])
@login_required
def pickup_payment():
    def calculate_total_price(stuffs_count):
        return stuffs_count * 2000

    if request.method == 'POST':
        packed_stuffs = get_stuffs()
        if not packed_stuffs or len(packed_stuffs) == 0:
            return redirect(url_for('index'))

        order_info = get_order()
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

        user_pay_type = request.form.get('optionsPayType')

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
            tommorrow = today + timedelta(days=1)

            if converted_visit_date <= tommorrow or converted_revisit_date <= tommorrow:
                return bad_request(u'오후 5시가 넘어 내일을 방문예정일로 설정할 수 없습니다.')

        user_total_price = int(request.cookies.get('totalPrice'))
        total_price = calculate_total_price(len(packed_stuffs))

        if user_total_price != total_price:
            return redirect(url_for('schedule.estimate'))

        purchase = Purchase(
            status=PurchaseStatus.NORMAL,
            amount=total_price,
            pay_type=pay_types[user_pay_type],
            user_id=current_user.uid
        )

        database.session.add(purchase)

        committed_reservations = []
        for reservation in packed_stuffs:
            restore_reservation = RestoreReservation(
                status=ReservationStatus.WAITING,
                user_id=current_user.uid,
                contact=phone_number,
                address='%s %s' % (address1, address2),
                delivery_date=visit_date,
                delivery_time=visit_time,
                recovery_date=revisit_date,
                recovery_time=revisit_time,
                revisit_option=ReservationRevisitType.LATER if revisit_option == 'later' else ReservationRevisitType.IMMEDIATE,
                user_memo=user_memo,
                pay_type=pay_types[user_pay_type],
                goods_id=reservation.id,
                purchase_id=purchase.id
            )
            database.session.add(restore_reservation)
            committed_reservations.append(restore_reservation)

        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', 500)

        for reservation in committed_reservations:
            new_visit_schedule = Schedule(status=ScheduleStatus.WAITING,
                                          schedule_type=ScheduleType.RESTORE_DELIVERY,
                                          staff_id=1,
                                          customer_id=current_user.uid,
                                          schedule_date=visit_date,
                                          schedule_time_id=visit_time,
                                          reservation_id=reservation.id)
            database.session.add(new_visit_schedule)

            new_revisit_schedule = None
            if revisit_option == 'later':
                new_revisit_schedule = Schedule(status=ScheduleStatus.WAITING,
                                                schedule_type=ScheduleType.RESTORE_RECOVERY,
                                                staff_id=1,
                                                customer_id=current_user.uid,
                                                schedule_date=revisit_date,
                                                schedule_time_id=revisit_time,
                                                reservation_id=reservation.id)
            if new_revisit_schedule:
                database.session.add(new_revisit_schedule)

        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', 500)
        return response_template(u'정상 처리되었습니다', 200)

    packed_stuffs = get_stuffs()
    if not packed_stuffs or len(packed_stuffs) == 0:
        return redirect(url_for('index'))

    order_info = get_order()
    if not order_info:
        return redirect(url_for('index'))

    revisit_option = order_info['optionsRevisit']
    phone_number = order_info['inputPhoneNumber']
    visit_date = order_info['inputVisitDate']
    post_code = order_info['inputPostCode']
    address1 = order_info['inputAddress1']
    address2 = order_info['inputAddress2']
    visit_time = order_info['inputVisitTime']

    user_total_price = int(request.cookies.get('totalPrice'))
    total_price = calculate_total_price(len(packed_stuffs))

    if user_total_price != total_price:
        return redirect(url_for('schedule.estimate'))
    return render_template('pickup_payment.html', active_menu='reservation')


@payment.route('/delivery/payment', methods=['GET', 'POST'])
@login_required
def delivery_payment():
    def calculate_total_price(stuffs_count):
        return stuffs_count * 2000

    if request.method == 'POST':
        packed_stuffs = get_stuffs()
        if not packed_stuffs or len(packed_stuffs) == 0:
            return redirect(url_for('index'))

        order_info = get_order()
        if not order_info:
            return redirect(url_for('index'))

        phone_number = order_info.get('inputPhoneNumber')
        user_memo = order_info.get('textareaMemo')
        post_code = order_info.get('inputPostCode')
        address1 = order_info.get('inputAddress1')
        address2 = order_info.get('inputAddress2')
        delivery_option = order_info.get('optionsDelivery')
        visit_date = order_info.get('inputDeliveryDate')
        visit_time = order_info.get('inputDeliveryTime')

        user_pay_type = request.form.get('optionsPayType')

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

        start_time = escape(session.get('start_time'))
        converted_start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        day_standard_time1 = converted_start_time.replace(hour=17, minute=0)  # 저녁 5시 기준
        day_standard_time2 = converted_start_time.replace(hour=23, minute=59, second=59)

        if converted_start_time > day_standard_time1 and converted_start_time <= day_standard_time2:
            converted_visit_date = datetime.datetime.strptime(visit_date, "%Y-%m-%d")
            today = datetime.datetime.now()
            tommorrow = today + timedelta(days=1)

            if converted_visit_date <= tommorrow:
                return bad_request(u'오후 5시가 넘어 내일을 방문예정일로 설정할 수 없습니다.')

        user_total_price = int(request.cookies.get('totalPrice'))
        total_price = calculate_total_price(len(packed_stuffs))

        if user_total_price != total_price:
            return redirect(url_for('schedule.estimate'))

        purchase = Purchase(
            status=PurchaseStatus.NORMAL,
            amount=total_price,
            pay_type=pay_types[user_pay_type],
            user_id=current_user.uid
        )

        database.session.add(purchase)

        committed_reservations = []
        for reservation in packed_stuffs:
            delivery_reservation = DeliveryReservation(
                status=ReservationStatus.WAITING,
                user_id=current_user.uid,
                contact=phone_number,
                address='%s %s' % (address1, address2),
                delivery_option=1 if delivery_option == 'expire' else 0,
                delivery_date=visit_date,
                delivery_time=visit_time,
                user_memo=user_memo,
                pay_type=pay_types[user_pay_type],
                goods_id=reservation.id,
                purchase_id=purchase.id
            )
            database.session.add(delivery_reservation)
            committed_reservations.append(delivery_reservation)

        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', 500)

        for reservation in committed_reservations:
            new_visit_schedule = Schedule(status=ScheduleStatus.WAITING,
                                          schedule_type=ScheduleType.DELIVERY,
                                          staff_id=1,
                                          customer_id=current_user.uid,
                                          schedule_date=visit_date,
                                          schedule_time_id=visit_time,
                                          reservation_id=reservation.id)
            database.session.add(new_visit_schedule)

        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', 500)
        return response_template(u'정상 처리되었습니다', 200)

    packed_stuffs = get_stuffs()
    if not packed_stuffs or len(packed_stuffs) == 0:
        return redirect(url_for('index'))

    order_info = get_order()
    if not order_info:
        return redirect(url_for('index'))

    phone_number = order_info['inputPhoneNumber']
    user_memo = order_info['textareaMemo']
    post_code = order_info['inputPostCode']
    address1 = order_info['inputAddress1']
    address2 = order_info['inputAddress2']
    delivery_option = order_info['optionsDelivery']
    visit_date = order_info['inputDeliveryDate']
    visit_time = order_info['inputDeliveryTime']

    user_total_price = int(request.cookies.get('totalPrice'))
    total_price = calculate_total_price(len(packed_stuffs))

    if user_total_price != total_price:
        return redirect(url_for('schedule.estimate'))
    return render_template('delivery_payment.html', active_menu='reservation')


@payment.route('/extended/payment', methods=['GET', 'POST'])
@login_required
def extended_payment():
    def calculate_total_price():
        total_price = 0
        for goods_id in estimate_info.keys():
            if type(estimate_info[goods_id]) is int:
                if goods_id.startswith('B'):
                    total_price += (9900 * estimate_info[goods_id])
                else:
                    total_price += (7500 * estimate_info[goods_id])
            else:
                del estimate_info[goods_id]

        return total_price

    if request.method == 'POST':
        estimate_info = request.cookies.get('estimate')
        order_info = request.cookies.get('order')
        user_pay_type = request.form.get('optionsPayType')

        if not estimate_info or not order_info:
            return redirect(url_for('book.my_stuff'))

        estimate_info = json.loads(estimate_info)
        order_info = json.loads(order_info)

        start_time = order_info.get('start_time')
        user_total_price = order_info.get('total_price')

        try:
            datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            user_total_price = int(user_total_price)
        except:
            return response_template(u'잘못된 요청입니다.', status=400)

        total_price = calculate_total_price()
        if user_total_price != total_price:
            return response_template(u'잘못된 요청입니다.', status=400)

        stuffs = Goods.query.filter(
            Goods.goods_id.in_(estimate_info.keys())
        ).limit(10).all()

        packed_stuffs = []
        for item in stuffs:
            item.expired_at = add_months(item.expired_at, estimate_info[item.goods_id])
            packed_stuffs.append(item)

        if len(packed_stuffs) == 0:
            return response_template(u'잘못된 요청입니다.', status=400)

        purchase = Purchase(
            status=PurchaseStatus.NORMAL,
            amount=total_price,
            pay_type=pay_types[user_pay_type],
            user_id=current_user.uid
        )

        try:
            database.session.add(purchase)
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', status=500)
        return response_template(u'정상 처리되었습니다', status=200)

    estimate_info = request.cookies.get('estimate')
    order_info = request.cookies.get('order')

    if not estimate_info or not order_info:
        return redirect(url_for('book.my_stuff'))

    estimate_info = json.loads(estimate_info)
    order_info = json.loads(order_info)

    start_time = order_info.get('start_time')
    user_total_price = order_info.get('total_price')

    if not start_time or not user_total_price:
        return redirect(url_for('book.my_stuff'))

    try:
        datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        user_total_price = int(user_total_price)
    except:
        return response_template(u'잘못된 요청입니다.', status=400)

    total_price = calculate_total_price()
    if user_total_price != total_price:
        return redirect(url_for('book.my_stuff'))
    return render_template('extended_payment.html', active_menu='reservation')


@payment.route('/reservation/payment', methods=['GET', 'POST'])
@login_required
def reservation_payment():
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

    if request.method == 'POST':
        estimate_info = get_estimate()
        regular_item_count = estimate_info.get('regularItemNumberCount')
        irregular_item_count = estimate_info.get('irregularItemNumberCount')
        period = estimate_info.get('disposableNumberCount')
        period_option = estimate_info.get('optionsPeriod')
        binding_product0_count = estimate_info.get('bindingProduct0NumberCount')
        binding_product1_count = estimate_info.get('bindingProduct1NumberCount')
        binding_product2_count = estimate_info.get('bindingProduct2NumberCount')
        binding_product3_count = estimate_info.get('bindingProduct3NumberCount')
        promotion = estimate_info.get('inputPromotion')

        order_info = get_order()
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

        user_pay_type = request.form.get('optionsPayType')

        try:
            regular_item_count = int(regular_item_count)
            binding_product0_count = int(binding_product0_count)
            binding_product1_count = int(binding_product1_count)
            binding_product2_count = int(binding_product2_count)
            binding_product3_count = int(binding_product3_count)
            if period_option == 'disposable':
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

        start_time = escape(session.get('start_time'))

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

        user_total_price = int(request.cookies.get('totalPrice'))
        total_price = calculate_total_price()

        if user_total_price != total_price:
            return redirect(url_for('schedule.estimate'))

        purchase = Purchase(
            status=PurchaseStatus.NORMAL,
            amount=total_price,
            pay_type=pay_types[user_pay_type],
            user_id=current_user.uid
        )

        database.session.add(purchase)

        new_reservation = NewReservation(
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
            revisit_option=ReservationRevisitType.LATER if revisit_option == 'later' else ReservationRevisitType.IMMEDIATE,
            user_memo=user_memo,
            pay_type=pay_types[user_pay_type],
            user_id=current_user.uid,
            purchase_id=purchase.id
        )

        database.session.add(new_reservation)

        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', 500)

        new_visit_schedule = Schedule(status=ScheduleStatus.WAITING,
                                      schedule_type=ScheduleType.PICKUP_DELIVERY,
                                      staff_id=1,
                                      customer_id=current_user.uid,
                                      schedule_date=visit_date,
                                      schedule_time_id=visit_time,
                                      reservation_id=new_reservation.id)
        database.session.add(new_visit_schedule)

        new_revisit_schedule = None
        if revisit_option == 'later':
            new_revisit_schedule = Schedule(status=ScheduleStatus.WAITING,
                                            schedule_type=ScheduleType.PICKUP_RECOVERY,
                                            staff_id=1,
                                            customer_id=current_user.uid,
                                            schedule_date=revisit_date,
                                            schedule_time_id=revisit_time,
                                            reservation_id=new_reservation.id)
        if new_revisit_schedule:
            database.session.add(new_revisit_schedule)

        logged_in_user = User.query.get(current_user.uid)
        logged_in_user.phone = phone_number
        logged_in_user.address1 = address1
        logged_in_user.address2 = address2

        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', 500)
        return response_template(u'정상 처리되었습니다', 200)

    estimate_info = get_estimate()
    regular_item_count = estimate_info.get('regularItemNumberCount')
    irregular_item_count = estimate_info.get('irregularItemNumberCount')
    period = estimate_info.get('disposableNumberCount')
    period_option = estimate_info.get('optionsPeriod')
    binding_product0_count = estimate_info.get('bindingProduct0NumberCount')
    binding_product1_count = estimate_info.get('bindingProduct1NumberCount')
    binding_product2_count = estimate_info.get('bindingProduct2NumberCount')
    binding_product3_count = estimate_info.get('bindingProduct3NumberCount')

    try:
        estimate_info.get('startTime')
        request.cookies['totalPrice']
    except:
        return redirect(url_for('schedule.estimate'))

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
        return redirect(url_for('schedule.estimate'))

    user_total_price = int(request.cookies.get('totalPrice'))
    total_price = calculate_total_price()

    if user_total_price != total_price:
        return redirect(url_for('schedule.estimate'))
    return render_template('reservation_payment.html', active_menu='reservation')

