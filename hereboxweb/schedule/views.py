# -*- coding: utf-8 -*-


from flask import request, render_template, redirect, url_for, make_response, session, escape, jsonify
from flask_login import login_required, current_user
from flask_mobility.decorators import mobile_template
from sqlalchemy import or_, func
from sqlalchemy.orm import aliased
from hereboxweb import response_template, bad_request, forbidden
from hereboxweb.admin.models import VisitTime
from hereboxweb.book.stuffs import save_stuffs, get_stuffs
from hereboxweb.payment.models import Purchase, PayType
from hereboxweb.schedule import schedule
from hereboxweb.schedule.delivery import calculate_total_delivery_price, \
    DeliverySerializableFactory, DeliveryOption
from hereboxweb.schedule.models import *
from hereboxweb.schedule.price import calculate_storage_price, calculate_total_price
from hereboxweb.schedule.purchase_step import PurchaseStepManager, CookieSerializableStoreManager
from hereboxweb.schedule.reservation import ReservationSerializableFactory, RevisitOption, PeriodOption
from sqlalchemy.orm import with_polymorphic

SCHEDULE_LIST_MAX_COUNT = 10


@schedule.route('/my_schedule', methods=['GET'])
@mobile_template('{mobile/}my_schedule.html')
@login_required
def my_schedule(template):
    staff = aliased(User, name="staff")
    customer = aliased(User, name="customer")

    my_pickup_schedules = database.session.query(
        Schedule,
        staff.name.label("staff_name"),
        customer.name.label("customer_name")).join((staff, Schedule.staff),
                                                  (customer, Schedule.customer)
                                                   ).filter(
        Schedule.customer_id == current_user.uid,
        or_(Schedule.schedule_type == ScheduleType.PICKUP_DELIVERY,
            Schedule.schedule_type == ScheduleType.PICKUP_RECOVERY,
            Schedule.schedule_type == ScheduleType.RESTORE_DELIVERY,
            Schedule.schedule_type == ScheduleType.RESTORE_RECOVERY,),
        Schedule.status == ScheduleStatus.WAITING
    ).order_by(Schedule.updated_at.desc()).limit(SCHEDULE_LIST_MAX_COUNT).all()

    packed_my_pickup = []
    for item in my_pickup_schedules:
        packed_my_pickup.append(item[0])

    my_delivery_schedules = database.session.query(
        Schedule,
        staff.name.label("staff_name"),
        customer.name.label("customer_name")).join((staff, Schedule.staff),
                                                   (customer, Schedule.customer)
                                                   ).filter(
        Schedule.customer_id == current_user.uid,
        Schedule.schedule_type == ScheduleType.DELIVERY,
        Schedule.status == ScheduleStatus.WAITING
    ).order_by(Schedule.updated_at.desc()).limit(SCHEDULE_LIST_MAX_COUNT).all()

    packed_my_delivery = []
    for item in my_delivery_schedules:
        packed_my_delivery.append(item[0])

    return render_template(template, active_my_index='my_schedule',
                           packed_my_pickup=packed_my_pickup,
                           packed_my_delivery=packed_my_delivery)


@schedule.route('/reservation/estimate', methods=['GET', 'POST'])
@mobile_template('{mobile/}estimate.html')
@login_required
def estimate(template):
    cookie_store_manager = CookieSerializableStoreManager()
    if request.method == 'POST':
        order_helper = ReservationSerializableFactory.serializable('order')
        order_manager = PurchaseStepManager(order_helper, cookie_store_manager)
        response = make_response(response_template(u'정상 처리되었습니다'))
        return order_manager.save(request.form, response, '/reservation/')

    estimate_helper = ReservationSerializableFactory.serializable('estimate')
    estimate_manager = PurchaseStepManager(estimate_helper, cookie_store_manager)
    try:
        user_estimate = estimate_manager.get(request.cookies)
        if user_estimate:
            return make_response(render_template(template, active_menu='reservation',
                             regular_item_count=user_estimate.regular_item_count,
                             irregular_item_count=user_estimate.irregular_item_count,
                             period=user_estimate.period,
                             period_option=user_estimate.period_option,
                             binding_product0_count=user_estimate.binding_product0_count,
                             binding_product1_count=user_estimate.binding_product1_count,
                             binding_product2_count=user_estimate.binding_product2_count,
                             binding_product3_count=user_estimate.binding_product3_count,
                             promotion=user_estimate.promotion))
        session['start_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return render_template(template, active_menu='reservation')
    except KeyError as error:
        return bad_request(error.message)
    except ValueError:
        return bad_request()



@schedule.route('/reservation/order', methods=['GET', 'POST'])
@mobile_template('{mobile/}reservation.html')
@login_required
def order(template):
    estimate_helper = ReservationSerializableFactory.serializable('estimate')
    cookie_store_manager = CookieSerializableStoreManager()
    estimate_manager = PurchaseStepManager(estimate_helper, cookie_store_manager)
    if request.method == 'POST':
        response = make_response(response_template(u'정상 처리되었습니다'))
        return estimate_manager.save(request.form, response, '/reservation/')

    try:
        user_estimate = estimate_manager.get(request.cookies)
        if calculate_storage_price(user_estimate.regular_item_count, user_estimate.irregular_item_count,
                                   user_estimate.period_option, user_estimate.period) <= 0:
            return bad_request(u'하나 이상의 상품을 구매하셔야 합니다.')
    except KeyError as error:
        return bad_request(error.message)
    except ValueError:
        return bad_request()

    order_helper = ReservationSerializableFactory.serializable('order')
    order_manager = PurchaseStepManager(order_helper, cookie_store_manager)

    try:
        user_order = order_manager.get(request.cookies)
        if user_order:
            return make_response(
                render_template(template, active_menu='reservation', old_phone_number=current_user.phone,
                                address1=user_order.address1,
                                address2=user_order.address2,
                                user_memo=user_order.user_memo))
        return make_response(
            render_template(template, active_menu='reservation', old_phone_number=current_user.phone))
    except KeyError as error:
        return bad_request(error.message)
    except ValueError:
        return bad_request()


@schedule.route('/reservation/review', methods=['GET', 'POST'])
@mobile_template('{mobile/}review.html')
@login_required
def review(template):
    cookie_store_manager = CookieSerializableStoreManager()
    if request.method == 'POST':
        order_helper = ReservationSerializableFactory.serializable('order')
        order_manager = PurchaseStepManager(order_helper, cookie_store_manager)
        response = make_response(response_template(u'정상 처리되었습니다'))
        return order_manager.save(request.form, response, '/reservation/')

    estimate_helper = ReservationSerializableFactory.serializable('estimate')
    estimate_manager = PurchaseStepManager(estimate_helper, cookie_store_manager)
    try:
        user_estimate = estimate_manager.get(request.cookies)
        if not user_estimate:
            return redirect(url_for('index'))
    except KeyError as error:
        return bad_request(error.message)
    except ValueError:
        return bad_request()

    start_time = escape(session.get('start_time'))
    if not start_time:
        return redirect(url_for('index'))

    order_helper = ReservationSerializableFactory.serializable('order')
    order_manager = PurchaseStepManager(order_helper, cookie_store_manager)
    try:
        user_order = order_manager.get(request.cookies)
        if not user_order:
            return redirect(url_for('index'))
    except KeyError as error:
        return bad_request(error.message)
    except ValueError:
        return bad_request()

    visit_time = VisitTime.query.get(user_order.visit_time)
    revisit_time = None
    if user_order.revisit_option == RevisitOption.LATER:
        revisit_time = VisitTime.query.get(user_order.revisit_time)

    promotion_name = None
    promotion_code = PromotionCode.query.filter(PromotionCode.code == user_estimate.promotion).first()
    if promotion_code:
        promotion_name = promotion_code.promotion.name

    total_price = calculate_total_price(
        user_estimate.regular_item_count, user_estimate.irregular_item_count, user_estimate.period,
        user_estimate.period_option, user_estimate.promotion, user_estimate.binding_product0_count,
        user_estimate.binding_product1_count, user_estimate.binding_product2_count,
        user_estimate.binding_product3_count)

    response = make_response(render_template(template, active_menu='reservation',
                 standard_box_count=user_estimate.regular_item_count,
                 nonstandard_goods_count=user_estimate.irregular_item_count,
                 period_option=True if user_estimate.period_option == PeriodOption.SUBSCRIPTION else False,
                 period=user_estimate.period,
                 binding_products={u'포장용 에어캡 1m': user_estimate.binding_product0_count,
                                   u'실리카겔 (제습제) 50g': user_estimate.binding_product1_count,
                                   u'압축팩 40cm x 60cm': user_estimate.binding_product2_count,
                                   u'테이프 48mm x 40m': user_estimate.binding_product3_count},
                 promotion=promotion_name,
                 total_price=u'{:,d}원'.format(total_price),
                 phone=user_order.phone_number,
                 address='%s %s' % (user_order.address1, user_order.address2),
                 visit_date=user_order.visit_date,
                 visit_time=visit_time,
                 revisit_option=True if user_order.revisit_option == RevisitOption.LATER else False,
                 revisit_date=user_order.revisit_date,
                 revisit_time=revisit_time,
                 user_memo=user_order.user_memo))
    response.set_cookie('totalPrice', '%d' % (total_price), path='/reservation/')
    return response


@schedule.route('/reservation/completion', methods=['GET'])
@mobile_template('{mobile/}completion.html')
@login_required
def completion(template):
    return render_template(template, active_menu='reservation')


@schedule.route('/delivery/order', methods=['GET', 'POST'])
@login_required
@mobile_template('{mobile/}delivery_reservation.html')
def delivery_order(template):
    if request.method == 'POST':
        return save_stuffs('/delivery/')

    packed_stuffs = get_stuffs()
    if not packed_stuffs or len(packed_stuffs) == 0:
        return redirect(url_for('index'))

    order_helper = DeliverySerializableFactory.serializable('order')
    cookie_store_manager = CookieSerializableStoreManager()
    order_manager = PurchaseStepManager(order_helper, cookie_store_manager)
    try:
        user_order = order_manager.get(request.cookies)
        if not user_order:
            session['start_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return make_response(
                render_template(template, active_menu='reservation',
                                                    phone_number=current_user.phone))
        return make_response(
            render_template(template, active_menu='reservation',
                            phone_number=current_user.phone,
                            address1=user_order.address1,
                            address2=user_order.address2,
                            user_memo=user_order.user_memo))
    except KeyError as error:
        return bad_request(error.message)
    except ValueError:
        return bad_request()


@schedule.route('/delivery/review', methods=['GET', 'POST'])
@login_required
@mobile_template('{mobile/}delivery_review.html')
def delivery_review(template):
    cookie_store_manager = CookieSerializableStoreManager()
    if request.method == 'POST':
        if not session.pop('phone_authentication', False):
            return forbidden(u'핸드폰 번호 인증을 먼저 해주세요')

        order_helper = DeliverySerializableFactory.serializable('order')
        order_manager = PurchaseStepManager(order_helper, cookie_store_manager)
        response = make_response(response_template(u'정상 처리되었습니다'))
        return order_manager.save(request.form, response, '/delivery/')

    packed_stuffs = get_stuffs()
    if not packed_stuffs or len(packed_stuffs) == 0:
        return redirect(url_for('index'))

    order_helper = DeliverySerializableFactory.serializable('order')
    order_manager = PurchaseStepManager(order_helper, cookie_store_manager)
    try:
        user_order = order_manager.get(request.cookies)
        if not user_order:
            return redirect(url_for('index'))
    except KeyError as error:
        return bad_request(error.message)
    except ValueError:
        return bad_request()

    visit_time = VisitTime.query.get(user_order.visit_time)
    total_price = calculate_total_delivery_price(packed_stuffs)
    response = make_response(render_template(template, active_menu='reservation',
         packed_stuffs=packed_stuffs,
         delivery_option=u'재보관 가능' if user_order.delivery_option == DeliveryOption.RESTORE else u'보관 종료',
         address=u'%s %s' % (user_order.address1, user_order.address2),
         phone_number=user_order.phone_number,
         visit_date_time=u'%s %s' % (user_order.visit_date, visit_time),
         user_memo=user_order.user_memo,
         total_price=u'{:,d}원'.format(total_price))
        )
    response.set_cookie('totalPrice', '%d' % (total_price), path='/delivery/')
    return response


@schedule.route('/delivery/completion', methods=['GET'])
@login_required
@mobile_template('{mobile/}delivery_completion.html')
def delivery_completion(template):
    return render_template(template, active_menu='reservation')


@schedule.route('/pickup/order', methods=['GET', 'POST'])
@login_required
def pickup_order():
    if request.method == 'POST':
        return save_stuffs('/pickup/')

    packed_stuffs = get_stuffs()
    if not packed_stuffs or len(packed_stuffs) == 0:
        return redirect(url_for('index'))

    order_helper = ReservationSerializableFactory.serializable('order')
    cookie_store_manager = CookieSerializableStoreManager()
    order_manager = PurchaseStepManager(order_helper, cookie_store_manager)
    try:
        user_order = order_manager.get(request.cookies)
        if not user_order:
            session['start_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return make_response(
                render_template('pickup_reservation.html', active_menu='reservation',
                                                    phone_number=current_user.phone))
        return make_response(
            render_template('pickup_reservation.html', active_menu='reservation',
                            phone_number=current_user.phone,
                            address1=user_order.address1,
                            address2=user_order.address2,
                            user_memo=user_order.user_memo))
    except KeyError as error:
        return bad_request(error.message)
    except ValueError:
        return bad_request()


@schedule.route('/pickup/review', methods=['GET', 'POST'])
@login_required
def pickup_review():
    cookie_store_manager = CookieSerializableStoreManager()
    if request.method == 'POST':
        order_helper = ReservationSerializableFactory.serializable('order')
        order_manager = PurchaseStepManager(order_helper, cookie_store_manager)
        response = make_response(response_template(u'정상 처리되었습니다'))
        return order_manager.save(request.form, response, '/pickup/')

    packed_stuffs = get_stuffs()
    if not packed_stuffs or len(packed_stuffs) == 0:
        return redirect(url_for('index'))

    order_helper = ReservationSerializableFactory.serializable('order')
    order_manager = PurchaseStepManager(order_helper, cookie_store_manager)
    try:
        user_order = order_manager.get(request.cookies)
        if not user_order:
            return redirect(url_for('index'))
    except KeyError as error:
        return bad_request(error.message)
    except ValueError:
        return bad_request()

    visit_time = VisitTime.query.get(user_order.visit_time)
    revisit_time = None
    if user_order.revisit_option == RevisitOption.LATER:
        revisit_time = VisitTime.query.get(user_order.revisit_time)
    total_price = calculate_total_delivery_price(packed_stuffs)
    response = make_response(render_template('pickup_review.html', active_menu='reservation',
                         packed_stuffs=packed_stuffs,
                         phone_number=user_order.phone_number,
                         address=u'%s %s' % (user_order.address1, user_order.address2),
                         visit_date_time=u'%s %s' % (user_order.visit_date, visit_time),
                         revisit_option=True if user_order.revisit_option == RevisitOption.LATER else False,
                         revisit_date_time=u'%s %s' % (user_order.revisit_date, revisit_time),
                         user_memo=user_order.user_memo,
                         total_price=u'{:,d}원'.format(total_price))
                        )
    response.set_cookie('totalPrice', '%d' % (total_price), path='/pickup/')
    return response


@schedule.route('/pickup/completion', methods=['GET'])
@login_required
def pickup_completion():
    return render_template('completion.html', active_menu='reservation')


@schedule.route('/schedule/cancel', methods=['DELETE'])
@login_required
def cancel_schedule():
    schedule_id = request.form.get('schedule_id')

    schedule = Schedule.query.filter(Schedule.reservation_id == schedule_id,
                                     Schedule.customer_id == current_user.uid).first()

    if not schedule:
        return bad_request(u'찾을 수 없는 주문입니다.')

    schedule.status = ScheduleStatus.CANCELED

    try:
        database.session.commit()
    except:
        return response_template(u'문제가 발생했습니다. 나중에 다시시도 해주세요.', status=500)
    return response_template(u'정상적으로 처리되었습니다.')


@schedule.route('/promotion/<code>', methods=['GET'])
@login_required
def check_promotion(code):
    promotion_code = PromotionCode.query.join(Promotion).filter(
        PromotionCode.code == func.binary(code)).first()
    if not promotion_code:
        return bad_request(u'유효하지 않는 프로모션입니다.')

    today = datetime.datetime.now()
    if today > promotion_code.promotion.expired_at:
        return forbidden(u'유효 기간이 지난 프로모션입니다.')

    promotion_histories = PromotionHistory.query.join(PromotionCode).filter(
        PromotionHistory.user_id==current_user.uid)
    for history in promotion_histories:
        # 코드가 같을 경우
        if history.promotion_code.id == promotion_code.id:
            return forbidden(u'이미 사용한 적이 있는 프로모션입니다.')
        # 프로모션 자체가 같을 경우
        if history.promotion_code.promotion_id == promotion_code.promotion_id:
            return forbidden(u'이미 사용한 적이 있는 프로모션입니다.')

    promotion_obj = promotion_code.promotion
    from hereboxweb.schedule.promotion import ApplyPromotionManager
    apply_promotion = ApplyPromotionManager.apply(promotion_obj)

    response = jsonify(content = {'message': u'사용할 수 있는 프로모션입니다.', 'url': apply_promotion.__url__})
    response.set_cookie('promotion', promotion_code.code, path='/reservation/')
    return response


pay_types = {
    PayType.DIRECT: u'현장결제',
    PayType.CARD: u'카드결제',
    PayType.PHONE: u'휴대폰결제',
    PayType.KAKAOPAY: u'카카오페이',
}


pay_status = [u'완료', u'미완료']


@schedule.route('/reservation/<reservation_id>', methods=['GET'])
@login_required
@mobile_template('{mobile/}reservation_receipt.html')
def reservation_receipt(template, reservation_id):
    if not reservation_id:
        return render_template('404.html')

    entity = with_polymorphic(Reservation, NewReservation)
    reservation = database.session.query(entity).join(Purchase, User). \
        filter(Reservation.reservation_id == reservation_id).first()
    if not reservation:
        return render_template('404.html')

    if current_user.uid != reservation.user.uid:
        return render_template('403.html')

    promotion_name = None
    promotion_code = PromotionCode.query.filter(PromotionCode.code == reservation.promotion).first()
    if promotion_code:
        promotion_name = promotion_code.promotion.name

    visit_time = VisitTime.query.get(reservation.delivery_time)
    revisit_time = None
    if reservation.revisit_option == 1:
        revisit_time = VisitTime.query.get(reservation.recovery_time)

    return render_template(template,
                           reservation_id=reservation_id,
                           pay_status=pay_status[reservation.purchase.status],
                           pay_type=pay_types[reservation.purchase.pay_type],
                           standard_box_count=reservation.standard_box_count,
                           nonstandard_goods_count=reservation.nonstandard_goods_count,
                           period_option=True if reservation.fixed_rate == 1 else False,
                           period=reservation.period,
                           binding_products=json.loads(reservation.binding_products),
                           promotion=promotion_name,
                           total_price=u'{:,d}원'.format(int(reservation.purchase.amount)),
                           phone=reservation.user.phone,
                           address='%s %s' % (reservation.user.address1, reservation.user.address2),
                           visit_date=reservation.delivery_date,
                           visit_time=visit_time,
                           revisit_option=True if reservation.revisit_option == RevisitOption.LATER else False,
                           revisit_date=reservation.recovery_date,
                           revisit_time=revisit_time,
                           user_memo=reservation.user_memo)


delivery_types = [u'재보관 가능', u'보관종료']


@schedule.route('/delivery/<reservation_id>', methods=['GET'])
@login_required
@mobile_template('{mobile/}delivery_receipt.html')
def delivery_receipt(template, reservation_id):
    entity = with_polymorphic(Reservation, DeliveryReservation)
    reservation = database.session.query(entity).join(Purchase, User).\
        filter(Reservation.reservation_id == reservation_id).first()
    if not reservation_id:
        return render_template('404.html')

    visit_time = VisitTime.query.get(reservation.delivery_time)
    packed_stuffs = reservation.goods

    return render_template(template,
                     delivery_type=delivery_types[reservation.delivery_option],
                     packed_stuffs=packed_stuffs,
                     reservation_id=reservation_id,
                     pay_status=pay_status[reservation.purchase.status],
                     pay_type=pay_types[reservation.purchase.pay_type],
                     total_price=u'{:,d}원'.format(int(reservation.purchase.amount)),
                     phone=reservation.user.phone,
                     address='%s %s' % (reservation.user.address1, reservation.user.address2),
                     visit_date=reservation.delivery_date,
                     visit_time=visit_time,
                     user_memo=reservation.user_memo)


@schedule.route('/pickup/<reservation_id>', methods=['GET'])
@login_required
@mobile_template('{mobile/}pickup_receipt.html')
def pickup_receipt(template, reservation_id):
    entity = with_polymorphic(Reservation, RestoreReservation)
    reservation = database.session.query(entity).join(Purchase, User).\
        filter(Reservation.reservation_id == reservation_id).first()
    if not reservation_id:
        return render_template('404.html')

    visit_time = VisitTime.query.get(reservation.delivery_time)
    revisit_time = None
    if reservation.revisit_option == 1:
        revisit_time = VisitTime.query.get(reservation.recovery_time)

    packed_stuffs = reservation.goods

    return render_template(template,
             packed_stuffs=packed_stuffs,
             reservation_id=reservation_id,
             pay_status=pay_status[reservation.purchase.status],
             pay_type=pay_types[reservation.purchase.pay_type],
             total_price=u'{:,d}원'.format(int(reservation.purchase.amount)),
             phone=reservation.user.phone,
             address='%s %s' % (reservation.user.address1, reservation.user.address2),
             visit_date=reservation.delivery_date,
             visit_time=visit_time,
             revisit_option=True if reservation.revisit_option == RevisitOption.LATER else False,
             revisit_date=reservation.recovery_date,
             revisit_time=revisit_time,
             user_memo=reservation.user_memo)



