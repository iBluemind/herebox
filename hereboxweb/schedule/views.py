# -*- coding: utf-8 -*-
import re

from datetime import timedelta
from flask import request, render_template, redirect, url_for
from flask.ext.login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from hereboxweb import database, response_template, bad_request
from hereboxweb.schedule import schedule
from hereboxweb.schedule.models import *


@schedule.route('/my_schedule', methods=['GET'])
@login_required
def my_schedule():
    return render_template('my_schedule.html', active_my_index='my_schedule')


@schedule.route('/reservation/estimate', methods=['GET'])
@login_required
def estimate():
    return render_template('estimate.html', active_menu='reservation')


@schedule.route('/reservation/order', methods=['GET'])
@login_required
def order():
    return render_template('reservation.html', active_menu='reservation', phone_number=current_user.phone)


@schedule.route('/reservation/review', methods=['GET', 'POST'])
@login_required
def review():
    if request.method == 'POST':
        revisit_option = request.form.get('optionsRevisit')
        regular_item_count = request.form.get('regularItemNumberCount')
        phone_number = request.form.get('inputPhoneNumber')
        binding_product0_count = request.form.get('bindingProduct0NumberCount')
        binding_product1_count = request.form.get('bindingProduct1NumberCount')
        binding_product2_count = request.form.get('bindingProduct2NumberCount')
        binding_product3_count = request.form.get('bindingProduct3NumberCount')
        revisit_time = request.form.get('inputRevisitTime')
        user_memo = request.form.get('textareaMemo')
        start_time = request.form.get('startTime')
        period = request.form.get('disposableNumberCount')
        revisit_date = request.form.get('inputRevisitDate')
        visit_date = request.form.get('inputVisitDate')
        post_code = request.form.get('inputPostCode')
        period_option = request.form.get('optionsPeriod')
        irregular_item_count = request.form.get('irregularItemNumberCount')
        address1 = request.form.get('inputAddress1')
        address2 = request.form.get('inputAddress2')
        visit_time = request.form.get('inputVisitTime')
        promotion = request.form.get('inputPromotion')

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
        day_standard_time1 = converted_start_time.replace(hour=17, minute=0)   # 저녁 5시 기준
        day_standard_time2 = converted_start_time.replace(hour=23, minute=59, second=59)

        print day_standard_time1.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        if converted_start_time > day_standard_time1 and converted_start_time <= day_standard_time2:
            converted_visit_date = datetime.datetime.strptime(visit_date, "%Y-%m-%d")
            converted_revisit_date = datetime.datetime.strptime(revisit_date, "%Y-%m-%d")
            today = datetime.datetime.now()
            tommorrow = today + timedelta(days=1)

            if converted_visit_date <= tommorrow or converted_revisit_date <= tommorrow:
                return bad_request(u'오후 5시가 넘어 내일을 방문예정일로 설정할 수 없습니다.')

        new_reservation = Reservation(
            reservation_type=ReservationType.PICKUP_NEW,
            status=ReservationStatus.DRAFT,
            standard_box_count=regular_item_count,
            nonstandard_goods_count=irregular_item_count,
            period=period,
            fixed_rate=1 if period_option == 'subscription' else 0,
            promotion=promotion,
            binding_products={u'포장용 에어캡 1m': binding_product0_count, u'실리카겔 (제습제) 50g': binding_product1_count,
                              u'압축팩 40cm x 60cm': binding_product2_count, u'테이프 48mm x 40m': binding_product3_count},
            contact=phone_number,
            address='%s %s' % (address1, address2),
            delivery_date='%s %s' % (visit_date, visit_time),
            recovery_date='%s %s' % (revisit_date, revisit_time),
            user_memo=user_memo,
            user_id=current_user.uid,
        )

        try:
            old_reservation = Reservation.query.filter_by(reservation_id=new_reservation.reservation_id,
                                                          status=ReservationStatus.DRAFT,
                                                          user_id=current_user.uid).first()
            if old_reservation:
                old_reservation.standard_box_count = new_reservation.standard_box_count
                old_reservation.nonstandard_goods_count = new_reservation.nonstandard_goods_count
                old_reservation.period = new_reservation.period
                old_reservation.fixed_rate = new_reservation.fixed_rate
                old_reservation.promotion = new_reservation.promotion
                old_reservation.binding_products = new_reservation.binding_products
                old_reservation.contact = new_reservation.contact
                old_reservation.address = new_reservation.address
                old_reservation.delivery_date = new_reservation.delivery_date
                old_reservation.recovery_date = new_reservation.recovery_date
                old_reservation.user_memo = new_reservation.user_memo
                old_reservation.updated_at = datetime.datetime.now()
            else:
                database.session.add(new_reservation)
            database.session.commit()
        except :
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', 500)
        return response_template(u'정상 처리되었습니다', 200, data={'reservation_id': new_reservation.reservation_id})



    return render_template('review.html', active_menu='reservation')


@schedule.route('/reservation/completion', methods=['GET'])
@login_required
def completion():
    return render_template('completion.html', active_menu='reservation')