# -*- coding: utf-8 -*-


import datetime
from flask import request, render_template, make_response, url_for, redirect, flash
from flask.ext.login import login_user
from config import RSA_PUBLIC_KEY_BASE64
from hereboxweb import database, response_template, bad_request
from hereboxweb.admin import admin
from hereboxweb.auth.forms import LoginForm
from hereboxweb.auth.login import HereboxLoginHelper
from hereboxweb.auth.models import User, UserStatus
from hereboxweb.book.models import GoodsType, Box, Goods, InStoreStatus, GoodsStatus, BoxStatus
from hereboxweb.schedule.models import Reservation, ReservationStatus, ScheduleType, ScheduleStatus
from hereboxweb.utils import add_months, staff_required


@admin.route('/', methods=['GET'])
@staff_required
def admin_index():
    return render_template('admin_dashboard.html', page_title=u'대시보드',
                                                    page_subtitle='Overview',
                                                )


@admin.route('/login', methods=['GET', 'POST'])
def admin_login():
    form = LoginForm()
    rsa_public_key = RSA_PUBLIC_KEY_BASE64

    if form.validate_on_submit():
        encoded_email = form.email.data
        encoded_password = form.password.data
        encoded_aes_key = request.form['decryptKey']
        encoded_aes_iv = request.form['iv']

        herebox_login_helper = HereboxLoginHelper(encoded_email, encoded_password,
                                                  encoded_aes_key, encoded_aes_iv)

        try:
            decrypted_email, decrypted_password = herebox_login_helper.decrypt()
            query = database.session.query(User).filter(User.email == decrypted_email,
                                                        User.status >= UserStatus.STAFF)
            user = query.first()

            if user.check_password(decrypted_password):
                flash(u'환영합니다')
                login_user(user)
                return redirect(url_for('admin.admin_index'))
            else:
                raise
        except:
            form.email.errors.append(u'이메일 주소 또는 비밀번호를 다시 확인해주세요.')

    form.email.data = ''
    response = make_response(render_template('admin_login.html', form=form))
    response.set_cookie('jsessionid', rsa_public_key, path='/admin/login')
    return response


@admin.route('/reservation/accept', methods=['POST'])
# @staff_required
def accept_reservation():
    reservation_id = request.form.get('reservation_id')
    reservation = Reservation.query.filter(Reservation.reservation_id == reservation_id).first()
    if not reservation:
        return response_template(u'%s 주문을 찾을 수 없습니다.' % reservation_id, status=400)

    reservation.status = ReservationStatus.ACCEPTED

    try:
        database.session.commit()
    except:
        return response_template(u'오류가 발생했습니다.', status=500)
    return response_template(u'정상 처리되었습니다.')


@admin.route('/goods/allocate', methods=['POST'])
# @staff_required
def allocate_goods():
    goods_type = request.form.get('goods_type')
    reservation_id = request.form.get('reservation_id')
    name = request.form.get('name')
    box_id = request.form.get('box_id')
    memo = request.form.get('memo')
    user_id = request.form.get('uid')

    box = None
    if goods_type == GoodsType.STANDARD_BOX:
        box = Box.query.filter(Box.box_id == box_id, Box.status == BoxStatus.AVAILABLE).first()
        if not box:
            return response_template(u'%s 상자를 찾을 수 없습니다.' % box_id, status=400)

        box.status = BoxStatus.UNAVAILABLE

    reservation = Reservation.query.filter(
                        Reservation.reservation_id == reservation_id,
                        Reservation.status == ReservationStatus.ACCEPTED).first()
    if not reservation:
        return response_template(u'접수된 주문 %s을 찾을 수 없습니다.' % reservation_id, status=400)

    schedules = reservation.schedules
    pickup_schedules = []
    for schedule in schedules:
        if schedule.schedule_type == ScheduleType.PICKUP_DELIVERY or\
                schedule.schedule_type == ScheduleType.PICKUP_RECOVERY:
            schedule.status = ScheduleStatus.COMPLETE
            pickup_schedules.append(schedule)

    today = datetime.date.today()
    expired = add_months(today, reservation.period)

    new_goods = Goods(goods_type=goods_type,
                      name=name,
                      memo=memo,
                      in_store=InStoreStatus.IN_STORE,
                      box_id=box.id if box else None,
                      user_id=user_id,
                      schedules=pickup_schedules,
                      expired_at=expired,
                      fixed_rate=reservation.fixed_rate,
                      status=GoodsStatus.ACTIVE)

    try:
        database.session.add(new_goods)
        database.session.commit()
    except:
        return response_template(u'오류가 발생했습니다.', status=500)

    if goods_type == GoodsType.STANDARD_BOX:
        box.goods_id = new_goods.id

        try:
            database.session.commit()
        except:
            return response_template(u'오류가 발생했습니다.', status=500)

    return response_template(u'정상 처리되었습니다.')


@admin.route('/goods/store', methods=['POST'])
# @staff_required
def store_goods():
    goods_id = request.form.get('goods_id')

    goods = Goods.query.filter(Goods.goods_id == goods_id,
                                Goods.in_store == InStoreStatus.OUT_OF_STORE)\
                            .first()

    goods.in_store = InStoreStatus.IN_STORE

    try:
        database.session.commit()
    except:
        return response_template(u'오류가 발생했습니다.', status=500)
    return response_template(u'정상 처리되었습니다.')


@admin.route('/goods/release', methods=['POST'])
# @staff_required
def release_goods():
    goods_id = request.form.get('goods_id')

    goods = Goods.query.filter(Goods.goods_id == goods_id,
                                Goods.in_store == InStoreStatus.IN_STORE)\
                            .first()

    goods.in_store = InStoreStatus.OUT_OF_STORE

    try:
        database.session.commit()
    except:
        return response_template(u'오류가 발생했습니다.', status=500)
    return response_template(u'정상 처리되었습니다.')


@admin.route('/goods/free', methods=['POST'])
# @staff_required
def free_goods():
    goods_id = request.form.get('goods_id')

    today = datetime.date.today()
    goods = Goods.query.filter(
                               Goods.goods_id == goods_id,
                               today >= Goods.expired_at,
                               Goods.status == GoodsStatus.ACTIVE).first()

    if not goods:
        return bad_request(u'물품 %s를 찾을 수 없습니다.' % goods_id)

    if goods.box_id != None:
        box = Box.query.get(goods.box_id)
        box.goods_id = None
        box.status = BoxStatus.AVAILABLE
    goods.status = GoodsStatus.EXPIRED

    try:
        database.session.commit()
    except:
        return response_template(u'오류가 발생했습니다.', status=500)
    return response_template(u'정상 처리되었습니다.')