# -*- coding: utf-8 -*-


import json
import re
import datetime
from flask import request, escape, session, make_response, render_template
from flask.ext.login import current_user
from hereboxweb import bad_request, forbidden


def save_delivery_order():
    delivery_option = request.form.get('optionsDelivery')
    phone_number = request.form.get('inputPhoneNumber')
    user_memo = request.form.get('textareaMemo')
    post_code = request.form.get('inputPostCode')
    address1 = request.form.get('inputAddress1')
    address2 = request.form.get('inputAddress2')
    visit_date = request.form.get('inputDeliveryDate')
    visit_time = request.form.get('inputDeliveryTime')

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

    start_time = escape(session['start_time'])
    converted_start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    day_standard_time1 = converted_start_time.replace(hour=17, minute=0)  # 저녁 5시 기준
    day_standard_time2 = converted_start_time.replace(hour=23, minute=59, second=59)

    if converted_start_time > day_standard_time1 and converted_start_time <= day_standard_time2:
        converted_visit_date = datetime.datetime.strptime(visit_date, "%Y-%m-%d")
        today = datetime.datetime.now()
        tommorrow = today + datetime.timedelta(days=1)

        if converted_visit_date <= tommorrow:
            return bad_request(u'오후 5시가 넘어 내일을 방문예정일로 설정할 수 없습니다.')

    if not session.pop('phone_authentication', False):
        return forbidden(u'핸드폰 번호 인증을 먼저 해주세요')

    response = make_response(render_template('reservation.html', active_menu='reservation',
                                             phone_number=current_user.phone))

    order_info = {
        'optionsDelivery': delivery_option,
        'inputPhoneNumber': phone_number,
        'inputDeliveryDate': visit_date,
        'inputPostCode': post_code,
        'inputDeliveryTime': visit_time,
        'inputAddress1': address1,
        'inputAddress2': address2,
    }

    if user_memo != None:
        order_info['textareaMemo'] = user_memo
    response.set_cookie('order', json.dumps(order_info), path='/delivery/')
    return response