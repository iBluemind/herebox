# -*- coding: utf-8 -*-


import datetime
from flask import request, render_template, make_response, url_for, redirect, flash, json
from flask_login import login_user
from sqlalchemy import or_
from config import RSA_PUBLIC_KEY_BASE64
from hereboxweb import database, response_template, app
from hereboxweb.admin import admin
from hereboxweb.admin.models import VisitTime
from hereboxweb.auth.forms import LoginForm
from hereboxweb.auth.login import HereboxLoginHelper
from hereboxweb.auth.models import User, UserStatus
from hereboxweb.book.models import GoodsType, Box, Goods, InStoreStatus, GoodsStatus, BoxStatus, Incoming, Outgoing
from hereboxweb.payment.models import Purchase
from hereboxweb.schedule.models import Reservation, ReservationStatus, ScheduleType, ScheduleStatus, NewReservation, \
    ReservationType, RestoreReservation, DeliveryReservation, ReservationDeliveryType, Schedule, ReservationRevisitType, \
    ExtendPeriod, ExtendPeriodStatus, PromotionCode, UnavailableSchedule
from hereboxweb.schedule.reservation import RevisitOption
from hereboxweb.utils import add_months, staff_required
from hereboxweb.admin import custom_filter

USERS_PER_PAGE = 15
RESERVATIONS_PER_PAGE = 15
SCHEDULES_PER_PAGE = 15
PURCHASES_PER_PAGE = 10
BOXES_PER_PAGE = 15
GOODS_PER_PAGE = 15
EXTEND_PERIOD_PER_PAGE = 10
INCOMINGS_PER_PAGE = 30


@admin.route('/schedule_restriction', methods=['GET', 'POST', 'DELETE'])
@staff_required
def schedule_restriction():
    # 스케줄 제한 조회
    if request.method == 'GET':
        today = datetime.date.today()
        u_schedules = database.session.query(UnavailableSchedule, VisitTime) \
            .filter(UnavailableSchedule.schedule_time_id == VisitTime.id).filter(UnavailableSchedule.date >= today) \
            .order_by(UnavailableSchedule.date)

        return render_template('admin_schedule_restriction.html', u_schedules=u_schedules,
                               page_title=u'예약 제한', page_subtitle='Schedule Restriction')

    # 스케줄 제한 추가
    elif request.method == 'POST':
        date = request.form.get('date')
        time = request.form.get('time')
        u_schedule = UnavailableSchedule(date, time)
        database.session.add(u_schedule)
        try:
            database.session.commit()
        except:
            return redirect(url_for('admin.schedule_restriction'))
        return redirect(url_for('admin.schedule_restriction'))

    # 스케줄 제한 삭제
    elif request.method == 'DELETE':
        id = request.form.get('id')
        print id
        u_schedule = UnavailableSchedule.query.get(id)
        database.session.delete(u_schedule)
        try:
            print "TRY"
            database.session.commit()
            return response_template(u'삭제되었습니다.', status=200)
        except:
            print "ERROR"
            return response_template(u'문제가 발생했습니다.', status=500)


@admin.route('/outgoing/<int:page>', methods=['GET'])
@staff_required
def outgoing_history(page=1):
    paginate = Outgoing.query.join(Goods) \
        .order_by(Outgoing.created_at.desc()) \
        .paginate(page, INCOMINGS_PER_PAGE, False)

    return render_template('admin_outgoing_history.html', page_title=u'출고기록',
                           page_subtitle='Outgoing History',
                           pagination=paginate)


@admin.route('/incoming/<int:page>', methods=['GET'])
@staff_required
def incoming_history(page=1):
    paginate = Incoming.query.join(Goods) \
        .order_by(Incoming.created_at.desc()) \
        .paginate(page, INCOMINGS_PER_PAGE, False)

    return render_template('admin_incoming_history.html', page_title=u'입고기록',
                           page_subtitle='Incoming History',
                           pagination=paginate)


@admin.route('/extend-period/<int:extend_period_id>', methods=['PUT'])
@staff_required
def extend_period(extend_period_id):
    extend_period = ExtendPeriod.query.filter(ExtendPeriod.id == extend_period_id).first()

    extend_period.status = ExtendPeriodStatus.ACCEPTED
    extend_period.goods.expired_at = add_months(extend_period.goods.expired_at, extend_period.amount)

    try:
        database.session.commit()
    except:
        return response_template(u'문제가 발생했습니다.', status=500)
    return response_template(u'처리되었습니다', status=200)


@admin.route('/extend-periods/<int:page>', methods=['GET'])
@staff_required
def extend_period_list(page):
    paginate = ExtendPeriod.query.filter(ExtendPeriod.status == ExtendPeriodStatus.WAITING) \
        .order_by(ExtendPeriod.created_at.desc()) \
        .paginate(page, EXTEND_PERIOD_PER_PAGE, False)

    return render_template('admin_extend_period_list.html', page_title=u'기간연장',
                           page_subtitle='Extend Period',
                           pagination=paginate)


@admin.route('/old-extend-periods/<int:page>', methods=['GET'])
@staff_required
def old_extend_period_list(page):
    paginate = ExtendPeriod.query.filter(ExtendPeriod.status==ExtendPeriodStatus.ACCEPTED) \
        .order_by(ExtendPeriod.created_at.desc()) \
        .paginate(page, EXTEND_PERIOD_PER_PAGE, False)

    return render_template('admin_old_extend_period_list.html', page_title=u'지난 기간연장',
                           page_subtitle='Old Extend Period',
                           pagination=paginate
                           )


@admin.route('/goods/<goods_id>', methods=['GET', 'POST', 'DELETE'])
@staff_required
def goods_detail(goods_id):
    goods = Goods.query.filter(Goods.goods_id==goods_id).first()
    if goods.goods_id.startswith('A'):
        goods.box = Box.query.get(goods.box_id)

    if request.method == 'POST':
        goods_type = request.form.get('goods_type')
        status = request.form.get('status')
        in_store = request.form.get('in_store')
        name = request.form.get('name')
        memo = request.form.get('memo')
        started_at = request.form.get('started_at')
        expired_at = request.form.get('expired_at')

        if goods_type and goods.goods_type != goods_type:
            goods.goods_type = goods_type
        if status and goods.status != status:
            goods.status = status
        if in_store and goods.in_store != in_store:
            goods.in_store = in_store
        if name and goods.name != name:
            goods.name = name
        if memo and goods.memo != memo:
            goods.memo = memo
        if started_at and goods.started_at != started_at:
            goods.started_at = started_at
        if expired_at and goods.expired_at != expired_at:
            expired_at = datetime.datetime.strptime(expired_at, '%Y-%m-%d').date()
            extended_period = (expired_at - goods.expired_at) / 30
            extend_period_history = ExtendPeriod(extended_period, goods.id, ExtendPeriodStatus.ACCEPTED)
            goods.expired_at = expired_at
            database.session.add(extend_period_history)

        incoming_history = Incoming(goods.id)
        database.session.add(incoming_history)

        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다.', status=500)

    if request.method == 'DELETE':
        if goods.box_id != None:
            box = Box.query.get(goods.box_id)
            box.goods_id = None
            box.status = BoxStatus.AVAILABLE
        goods.status = GoodsStatus.EXPIRED
        outgoing_history = Outgoing(goods.id)
        database.session.add(outgoing_history)

        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다.', status=500)

    return render_template('admin_goods.html', page_title=u'물품',
                           page_subtitle='Goods',
                           goods_detail=goods)


@admin.route('/schedule/<schedule_id>', methods=['GET', 'POST', 'DELETE'])
@staff_required
def schedule_detail(schedule_id):
    schedule = Schedule.query.filter(Schedule.schedule_id==schedule_id).first()
    schedule.parsed_schedule_time = VisitTime.query.get(schedule.schedule_time_id)
    if request.method == 'POST':
        visit_date = request.form.get('visit_date')
        if visit_date and schedule.schedule_date != visit_date:
            schedule.schedule_date = visit_date
        database.session.commit()

    if request.method == 'DELETE':
        schedule.status = ScheduleStatus.CANCELED
        try:
            database.session.commit()
            return redirect(url_for('admin.schedules'))
        except:
            return response_template(u'문제가 발생했습니다.', status=500)

    reservation = schedule.reservation
    if reservation.reservation_id.startswith(ReservationType.PICKUP_NEW):
        if (reservation.revisit_option == ReservationRevisitType.IMMEDIATE) or \
                (reservation.revisit_option == ReservationRevisitType.LATER and
                     schedule.schedule_id.endswith('_1')):
            return render_template('admin_schedule.html', page_title=u'스케줄',
                                   page_subtitle='Schedule',
                                   schedule_detail=schedule,
                                   register_goods_popup=True)
    return render_template('admin_schedule.html', page_title=u'스케줄',
                           page_subtitle='Schedule',
                           schedule_detail=schedule)


@admin.route('/goods_list/<int:page>', methods=['GET'])
@staff_required
def goods_list(page):
    paginate = Goods.query.order_by(Goods.created_at.desc()) \
        .paginate(page, GOODS_PER_PAGE, False)

    return render_template('admin_goods_list.html', page_title=u'물품조회',
                           page_subtitle='Goods',
                           pagination=paginate
                           )


@admin.route('/boxes/<int:page>', methods=['GET'])
@staff_required
def boxes(page):
    paginate = Box.query.order_by(Box.created_at.desc()) \
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
    ).order_by(Schedule.created_at.desc()) \
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
        ).order_by(Reservation.created_at.desc()) \
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
    paginate = Purchase.query.order_by(Purchase.created_at.desc()) \
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
    ).order_by(Schedule.created_at.desc()) \
        .paginate(page, SCHEDULES_PER_PAGE, False)

    for item in paginate.items:
        item.parsed_schedule_time = VisitTime.query.get(item.schedule_time_id)

    return render_template('admin_schedules.html', page_title=u'스케줄',
                           page_subtitle='Schedules',
                           pagination=paginate
                           )


@admin.route('/reservation/<reservation_id>', methods=['GET', 'POST', 'DELETE'])
@staff_required
def reservation_detail(reservation_id):
    reservation = None

    # 연락처, 주소 변경
    def change_reservation():
        if request.method == 'POST':
            contact = request.form.get('contact')
            address = request.form.get('address')

            if contact and reservation.contact != contact:
                reservation.contact = contact
            if address and reservation.address != address:
                reservation.address = address

            try:
                database.session.commit()
            except:
                return response_template(u'오류가 발생했습니다.', status=500)

    # New
    if reservation_id.startswith(ReservationType.PICKUP_NEW):
        # 새로운 예약
        reservation = NewReservation.query.filter(Reservation.reservation_id == reservation_id).first()

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

        promotion_code = PromotionCode.query.filter(PromotionCode.code == reservation.promotion).first()
        if promotion_code:
            reservation.promotion_name = u'%s(%s)' % (promotion_code.promotion.name,
                                                      reservation.promotion)
        # 신규 - 저장
        if request.method == 'POST':
            standard_box_count = request.form.get('standard_box_count')
            nonstandard_goods_count = request.form.get('nonstandard_goods_count')

            if standard_box_count and reservation.standard_box_count != int(standard_box_count):
                reservation.standard_box_count = int(standard_box_count)
            if nonstandard_goods_count and reservation.nonstandard_goods_count != int(nonstandard_goods_count):
                reservation.nonstandard_goods_count = int(nonstandard_goods_count)

        change_reservation()

        # 신규 - 삭제
        if request.method == 'DELETE':
            database.session.delete(reservation)
            try:
                database.session.commit()
                return redirect(url_for('admin.new_reservations'))
            except:
                return response_template(u'문제가 발생했습니다.', status=500)

        return render_template('admin_new_reservation.html', page_title=u'예약 정보',
                               page_subtitle='Reservation',
                               reservation_detail=reservation)
    # Pickup_again
    elif reservation_id.startswith(ReservationType.PICKUP_AGAIN):
        reservation = RestoreReservation.query.filter(Reservation.reservation_id==reservation_id).first()

        reservation.parsed_delivery_time = VisitTime.query.get(reservation.delivery_time)
        reservation.parsed_recovery_time = VisitTime.query.get(reservation.recovery_time)
        reservation.parsed_revisit_option = 'Y' if reservation.revisit_option == RevisitOption.LATER else 'N'

        change_reservation()

        if request.method == 'DELETE':
            database.session.delete(reservation)
            try:
                database.session.commit()
                return redirect(url_for('admin.restore_reservations'))
            except:
                return response_template(u'문제가 발생했습니다.', status=500)

        return render_template('admin_restore_reservation.html', page_title=u'예약 정보',
                               page_subtitle='Reservation',
                               reservation_detail=reservation)
    # Delivery
    elif reservation_id.startswith(ReservationType.DELIVERY):
        reservation = DeliveryReservation.query.filter(Reservation.reservation_id==reservation_id).first()

        reservation.parsed_delivery_time = VisitTime.query.get(reservation.delivery_time)
        reservation.parsed_delivery_option = 'Y' if reservation.delivery_option == ReservationDeliveryType.RESTORE else 'N'

        change_reservation()

        if request.method == 'DELETE':
            database.session.delete(reservation)
            try:
                database.session.commit()
                return redirect(url_for('admin.delivery_reservations'))
            except:
                return response_template(u'문제가 발생했습니다.', status=500)

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
    ).order_by(DeliveryReservation.created_at.desc()) \
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
    ).order_by(RestoreReservation.created_at.desc()) \
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
    ).order_by(NewReservation.created_at.desc()) \
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
    goods_expired_today = Goods.query.filter(Goods.expired_at <= today).count()
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
    reservation.updated_at = datetime.datetime.now()

    try:
        database.session.commit()
    except:
        return response_template(u'오류가 발생했습니다.', status=500)
    return response_template(u'정상 처리되었습니다.')


@admin.route('/schedule/register/goods', methods=['POST'])
@staff_required
def register_goods():
    schedule_id = request.form.get('schedule_id')
    schedule = Schedule.query.filter(Schedule.schedule_id == schedule_id).first()

    if not schedule:
        return response_template(u'%s 스케줄을 찾을 수 없습니다.' % schedule_id, status=400)

    reservation = schedule.reservation
    goods_type = request.form.get('goods_type')
    name = request.form.get('name')
    box_id = request.form.get('box_id')
    memo = request.form.get('memo')
    started_at = request.form.get('started_at')

    box = None
    if goods_type not in (GoodsType.STANDARD_BOX, GoodsType.NONSTANDARD_GOODS):
        return response_template(u'잘못된 규격입니다', status=400)

    if goods_type == GoodsType.STANDARD_BOX:
        box = Box.query.filter(Box.box_id == box_id, Box.status == BoxStatus.AVAILABLE).first()
        if not box:
            return response_template(u'%s 상자를 찾을 수 없습니다.' % box_id, status=400)

        box.status = BoxStatus.UNAVAILABLE

    try:
        started_at = datetime.datetime.strptime(started_at, "%Y-%m-%d")
    except:
        return response_template(u'잘못된 날짜형식입니다.', status=400)

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

    database.session.add(new_goods)
    reservation.goods.append(new_goods)

    try:
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


@admin.route('/schedule/complete', methods=['POST'])
@staff_required
def complete_schedule():
    schedule_id = request.form.get('schedule_id')
    schedule = Schedule.query.filter(Schedule.schedule_id == schedule_id).first()

    if not schedule:
        return response_template(u'%s 스케줄을 찾을 수 없습니다.' % schedule_id, status=400)

    reservation = schedule.reservation
    if reservation.status == ReservationStatus.WAITING:
        return response_template(u'%s 주문이 접수된 상태이어야 합니다!' % reservation.reservation_id, status=400)

    if reservation.reservation_id.startswith(ReservationType.PICKUP_NEW):
        if (reservation.revisit_option == ReservationRevisitType.IMMEDIATE) or \
                (reservation.revisit_option == ReservationRevisitType.LATER and
                     schedule.schedule_id.endswith('_1')):
            goods_count = len(reservation.goods)
            if goods_count == 0:
                return response_template(u'%s 주문에 등록된 물품이 없습니다!' % reservation.reservation_id, status=400)
            for goods in reservation.goods:
                incoming_history = Incoming(goods.id)
                database.session.add(incoming_history)
            schedules = reservation.schedules
            for schedule in schedules:
                if schedule.schedule_type == ScheduleType.PICKUP_DELIVERY or \
                                schedule.schedule_type == ScheduleType.PICKUP_RECOVERY:
                    schedule.status = ScheduleStatus.COMPLETE

    elif reservation.reservation_id.startswith(ReservationType.PICKUP_AGAIN):
        if (reservation.revisit_option == ReservationRevisitType.IMMEDIATE) or \
                (reservation.revisit_option == ReservationRevisitType.LATER and
                     schedule.schedule_id.endswith('_1')):
            for goods in reservation.goods:
                goods.in_store = InStoreStatus.IN_STORE
                incoming_history = Incoming(goods.id)
                database.session.add(incoming_history)
            schedules = reservation.schedules
            for schedule in schedules:
                if schedule.schedule_type == ScheduleType.RESTORE_DELIVERY or \
                                schedule.schedule_type == ScheduleType.RESTORE_RECOVERY:
                    schedule.status = ScheduleStatus.COMPLETE

    elif reservation.reservation_id.startswith(ReservationType.DELIVERY):
        for goods in reservation.goods:
            if reservation.delivery_option == ReservationDeliveryType.EXPIRE:
                if goods.box_id != None:
                    box = Box.query.get(goods.box_id)
                    box.goods_id = None
                    box.status = BoxStatus.AVAILABLE
                goods.status = GoodsStatus.EXPIRED
            else:
                goods.in_store = InStoreStatus.OUT_OF_STORE
            outgoing_history = Outgoing(goods.id)
            database.session.add(outgoing_history)

    schedule.status = ScheduleStatus.COMPLETE
    schedule.updated_at = datetime.datetime.now()

    try:
        database.session.commit()
    except:
        return response_template(u'오류가 발생했습니다.', status=500)
    return response_template(u'정상 처리되었습니다.')


