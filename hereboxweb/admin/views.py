# -*- coding: utf-8 -*-


import datetime

from flask import request, render_template, make_response, url_for, redirect, flash, json
from flask.ext.login import login_user
from sqlalchemy import or_
from sqlalchemy.orm import aliased

from config import RSA_PUBLIC_KEY_BASE64
from hereboxweb import database, response_template, bad_request
from hereboxweb.admin import admin
from hereboxweb.admin.models import VisitTime
from hereboxweb.auth.forms import LoginForm
from hereboxweb.auth.login import HereboxLoginHelper
from hereboxweb.auth.models import User, UserStatus
from hereboxweb.book.models import GoodsType, Box, Goods, InStoreStatus, GoodsStatus, BoxStatus
from hereboxweb.payment.models import Purchase
from hereboxweb.schedule.models import Reservation, ReservationStatus, ScheduleType, ScheduleStatus, NewReservation, \
    ReservationType, RestoreReservation, DeliveryReservation, ReservationDeliveryType, Schedule
from hereboxweb.schedule.reservation import RevisitOption
from hereboxweb.utils import add_months, staff_required


USERS_PER_PAGE = 10
RESERVATIONS_PER_PAGE = 10
SCHEDULES_PER_PAGE = 10
PURCHASES_PER_PAGE = 10
BOXES_PER_PAGE = 10
GOODS_PER_PAGE = 10


@admin.route('/goods/<goods_id>', methods=['GET', 'POST'])
@staff_required
def goods_detail(goods_id):
    goods = Goods.query.filter(Goods.goods_id==goods_id).first()
    if goods.goods_id.startswith('A'):
        goods.box = Box.query.get(goods.box_id)

    return render_template('admin_goods.html', page_title=u'물품',
                               page_subtitle='Goods',
                           goods_detail=goods)


@admin.route('/schedule/<schedule_id>', methods=['GET', 'POST'])
@staff_required
def schedule_detail(schedule_id):
    schedule = Schedule.query.filter(Schedule.schedule_id==schedule_id).first()
    schedule.parsed_schedule_time = VisitTime.query.get(schedule.schedule_time_id)

    return render_template('admin_schedule.html', page_title=u'스케줄',
                               page_subtitle='Schedule',
                               schedule_detail=schedule)


@admin.route('/goods_list/<int:page>', methods=['GET'])
@staff_required
def goods_list(page):
    paginate = Goods.query.order_by(Goods.created_at.desc())\
        .paginate(page, GOODS_PER_PAGE, False)

    return render_template('admin_goods_list.html', page_title=u'물품조회',
                                                    page_subtitle='Goods',
                                            pagination=paginate
    )


@admin.route('/boxes/<int:page>', methods=['GET'])
@staff_required
def boxes(page):
    paginate = Box.query.order_by(Box.created_at.desc())\
        .paginate(page, BOXES_PER_PAGE, False)

    return render_template('admin_boxes.html', page_title=u'박스현황',
                                                    page_subtitle='Boxes',
                                            pagination=paginate
    )


@admin.route('/old_schedules/<int:page>', methods=['GET'])
@staff_required
def old_schedules(page):
    paginate = Schedule.query.filter(
        or_(Schedule.status == ScheduleStatus.CANCELED,
            Schedule.status == ScheduleStatus.COMPLETE,)
    ).order_by(Schedule.created_at.desc())\
        .paginate(page, SCHEDULES_PER_PAGE, False)

    for item in paginate.items:
        item.parsed_schedule_time = VisitTime.query.get(item.schedule_time_id)

    return render_template('admin_old_schedules.html', page_title=u'지난 스케줄',
                                                    page_subtitle='Old Schedules',
                                            pagination=paginate
    )


@admin.route('/old_reservations/<int:page>', methods=['GET'])
@staff_required
def old_reservations(page):
    paginate = Reservation.query.filter(
        Reservation.status == ReservationStatus.ACCEPTED,
    ).order_by(Reservation.created_at.desc())\
        .paginate(page, RESERVATIONS_PER_PAGE, False)

    for item in paginate.items:
        item.parsed_delivery_time = VisitTime.query.get(item.delivery_time)

    return render_template('admin_old_reservations.html', page_title=u'지난 주문',
                                                    page_subtitle='Old Reservations',
                                            pagination=paginate
    )


@admin.route('/purchases/<int:page>', methods=['GET'])
@staff_required
def purchases(page):
    paginate = Purchase.query.order_by(Purchase.created_at.desc())\
        .paginate(page, PURCHASES_PER_PAGE, False)

    return render_template('admin_purchases.html', page_title=u'구매 히스토리',
                                                    page_subtitle='Purchase',
                                            pagination=paginate
    )


@admin.route('/schedules/<int:page>', methods=['GET'])
@staff_required
def schedules(page):
    paginate = Schedule.query.join(Schedule.customer).filter(
        Schedule.status == ScheduleStatus.WAITING
    ).order_by(Schedule.created_at.desc())\
        .paginate(page, SCHEDULES_PER_PAGE, False)

    for item in paginate.items:
        item.parsed_schedule_time = VisitTime.query.get(item.schedule_time_id)

    return render_template('admin_schedules.html', page_title=u'스케줄',
                                                    page_subtitle='Schedules',
                                            pagination=paginate
    )


@admin.route('/reservation/<reservation_id>', methods=['GET', 'POST'])
@staff_required
def reservation_detail(reservation_id):
    if reservation_id.startswith(ReservationType.PICKUP_NEW):
        reservation = NewReservation.query.filter(Reservation.reservation_id==reservation_id).first()

        parsed_binding_products = ''
        binding_products = json.loads(reservation.binding_products)
        for key in binding_products.keys():
            parsed_binding_products += '%s: ' % key
            parsed_binding_products += '%s ' % binding_products[key]
        reservation.parsed_binding_products = parsed_binding_products

        reservation.parsed_revisit_option = 'Y' if reservation.revisit_option == RevisitOption.LATER else 'N'
        reservation.parsed_fixed_rate = 'Y' if reservation.fixed_rate == 1 else 'N'

        reservation.parsed_delivery_time = VisitTime.query.get(reservation.delivery_time)
        reservation.parsed_recovery_time = VisitTime.query.get(reservation.recovery_time)

        return render_template('admin_new_reservation.html', page_title=u'예약 정보',
                               page_subtitle='Reservation',
                               reservation_detail=reservation)
    elif reservation_id.startswith(ReservationType.PICKUP_AGAIN):
        reservation = RestoreReservation.query.filter(Reservation.reservation_id==reservation_id).first()

        reservation.parsed_delivery_time = VisitTime.query.get(reservation.delivery_time)
        reservation.parsed_recovery_time = VisitTime.query.get(reservation.recovery_time)
        reservation.parsed_revisit_option = 'Y' if reservation.revisit_option == RevisitOption.LATER else 'N'

        return render_template('admin_restore_reservation.html', page_title=u'예약 정보',
                               page_subtitle='Reservation',
                               reservation_detail=reservation)
    elif reservation_id.startswith(ReservationType.DELIVERY):
        reservation = DeliveryReservation.query.filter(Reservation.reservation_id==reservation_id).first()

        reservation.parsed_delivery_time = VisitTime.query.get(reservation.delivery_time)
        reservation.parsed_delivery_option = 'Y' if reservation.delivery_option == ReservationDeliveryType.RESTORE else 'N'

        return render_template('admin_delivery_reservation.html', page_title=u'예약 정보',
                               page_subtitle='Reservation',
                               reservation_detail=reservation)


@admin.route('/user/<int:user_id>', methods=['GET', 'POST'])
@staff_required
def user_detail(user_id):
    user = User.query.get(user_id)
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        address1 = request.form.get('address1')
        address2 = request.form.get('address2')
        status = request.form.get('status')

        if name and user.name != name:
            user.name = name
        if email and user.email != email:
            user.email = email
        if address1 and user.address1 != address1:
            user.address1 = address1
        if address2 and user.address2 != address2:
            user.address2 = address2
        if status and user.status != status:
            user.status = status
        database.session.commit()
    return render_template('admin_user.html', page_title=u'회원 정보',
                                        page_subtitle='User',
                                       user_detail=user)


@admin.route('/delivery_reservations/<int:page>', methods=['GET'])
@staff_required
def delivery_reservations(page):
    paginate = DeliveryReservation.query.filter(
        DeliveryReservation.status == ReservationStatus.WAITING
    ).order_by(DeliveryReservation.created_at.desc())\
        .paginate(page, RESERVATIONS_PER_PAGE, False)

    for item in paginate.items:
        item.parsed_delivery_time = VisitTime.query.get(item.delivery_time)
        item.parsed_delivery_option = 'Y' if item.delivery_option == ReservationDeliveryType.RESTORE else 'N'

    return render_template('admin_delivery_reservations.html', page_title=u'배송',
                                                    page_subtitle='Delivery Reservations',
                                            pagination=paginate
    )


@admin.route('/restore_reservations/<int:page>', methods=['GET'])
@staff_required
def restore_reservations(page):
    paginate = RestoreReservation.query.filter(
        RestoreReservation.status == ReservationStatus.WAITING
    ).order_by(RestoreReservation.created_at.desc())\
        .paginate(page, RESERVATIONS_PER_PAGE, False)

    for item in paginate.items:
        item.parsed_delivery_time = VisitTime.query.get(item.delivery_time)
        item.parsed_revisit_option = 'Y' if item.revisit_option == RevisitOption.LATER else 'N'

    return render_template('admin_restore_reservations.html', page_title=u'재보관',
                                                    page_subtitle='Restore Reservations',
                                            pagination=paginate
    )


@admin.route('/new_reservations/<int:page>', methods=['GET'])
@staff_required
def new_reservations(page):
    paginate = NewReservation.query.filter(
        NewReservation.status == ReservationStatus.WAITING
    ).order_by(NewReservation.created_at.desc())\
        .paginate(page, RESERVATIONS_PER_PAGE, False)

    for item in paginate.items:
        parsed_binding_products = ''
        binding_products = json.loads(item.binding_products)
        for key in binding_products.keys():
            parsed_binding_products += '%s: ' % key
            parsed_binding_products += '%s ' % binding_products[key]
        item.parsed_binding_products = parsed_binding_products
        item.parsed_revisit_option = 'Y' if item.revisit_option == RevisitOption.LATER else 'N'

    return render_template('admin_new_reservations.html', page_title=u'신규픽업',
                                                    page_subtitle='New Reservations',
                                            pagination=paginate
    )


@admin.route('/', methods=['GET'])
@staff_required
def admin_index():
    today = datetime.date.today()
    reservations_today = Reservation.query.filter(Reservation.created_at >= today).count()
    goods_expired_today = Goods.query.filter(Goods.expired_at >= today).count()
    user_join_today = User.query.filter(User.created_at >= today).count()
    used_box_today = Box.query.filter(Box.status == BoxStatus.UNAVAILABLE).count()

    reservation_statistics = database.engine.execute(
        """
        SELECT CONCAT(
                  DATE_FORMAT(
                     DATE_SUB(created_at, INTERVAL (DAYOFWEEK(created_at) - 1) DAY),
                     "%%Y/%%m/%%d"),
                  ' ~ ',
                  DATE_FORMAT(
                     DATE_SUB(created_at, INTERVAL (DAYOFWEEK(created_at) - 7) DAY),
                     "%%Y/%%m/%%d"))
                  AS date,
               COUNT(*) AS count
          FROM `reservation`
        GROUP BY date
        ORDER BY `date` DESC
        """
    )

    reservation_statistics_data = []
    for row in reservation_statistics:
        reservation_statistics_data.append({
            "x": row[0],
            "y": row[1]
        })

    return render_template('admin_dashboard.html', page_title=u'대시보드',
                                                    page_subtitle='Overview',
                           reservations_today=reservations_today,
                           goods_expired_today=goods_expired_today,
                           user_join_today=user_join_today,
                           used_box_today=used_box_today,
                           reservation_statistics=json.dumps(reservation_statistics_data))


@admin.route('/users/<int:page>', methods=['GET'])
@staff_required
def admin_users(page):
    paginate = User.query.order_by(User.created_at.desc()).paginate(page, USERS_PER_PAGE, False)

    return render_template('admin_users.html', page_title=u'회원정보',
                                                    page_subtitle='Users',
                                            pagination=paginate
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
@staff_required
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
@staff_required
def allocate_goods():
    goods_type = request.form.get('goods_type')
    reservation_id = request.form.get('reservation_id')
    name = request.form.get('name')
    box_id = request.form.get('box_id')
    memo = request.form.get('memo')
    user_id = request.form.get('uid')
    started_at = request.form.get('started_at')
    expired_at = request.form.get('expired_at')
    fixed_rate = request.form.get('fixed_rate')

    box = None
    if goods_type == GoodsType.STANDARD_BOX:
        box = Box.query.filter(Box.box_id == box_id, Box.status == BoxStatus.AVAILABLE).first()
        if not box:
            return response_template(u'%s 상자를 찾을 수 없습니다.' % box_id, status=400)

        box.status = BoxStatus.UNAVAILABLE

    if fixed_rate:
        fixed_rate = int(fixed_rate)

    started_at = datetime.datetime.strptime(started_at, "%Y-%m-%d")

    if reservation_id:
        reservation = Reservation.query.filter(
                            Reservation.reservation_id == reservation_id,
                            Reservation.status == ReservationStatus.ACCEPTED).first()
        if not reservation:
            return response_template(u'접수된 주문 %s을 찾을 수 없습니다.' % reservation_id, status=400)

        schedules = reservation.schedules
        for schedule in schedules:
            if schedule.schedule_type == ScheduleType.PICKUP_DELIVERY or\
                    schedule.schedule_type == ScheduleType.PICKUP_RECOVERY:
                schedule.status = ScheduleStatus.COMPLETE

        user_id = reservation.user_id
        expired_at = add_months(started_at, reservation.period)
        fixed_rate = reservation.fixed_rate

    new_goods = Goods(goods_type=goods_type,
                      name=name,
                      memo=memo,
                      in_store=InStoreStatus.IN_STORE,
                      box_id=box.id if box else None,
                      user_id=user_id,
                      started_at=started_at,
                      expired_at=expired_at,
                      fixed_rate=fixed_rate,
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
@staff_required
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
@staff_required
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
@staff_required
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