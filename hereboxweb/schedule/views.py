# -*- coding: utf-8 -*-


from flask import request, render_template, redirect, url_for, make_response, session, escape, jsonify
from flask.ext.login import login_required, current_user
from flask.ext.mobility.decorators import mobile_template
from sqlalchemy import or_, func
from sqlalchemy.orm import aliased
from hereboxweb import response_template, bad_request, forbidden
from hereboxweb.admin.models import VisitTime
from hereboxweb.book.stuffs import save_stuffs, get_stuffs
from hereboxweb.schedule import schedule
from hereboxweb.schedule.delivery import calculate_total_delivery_price, \
    DeliverySerializableFactory, DeliveryOption
from hereboxweb.schedule.models import *
from hereboxweb.schedule.purchase_step import PurchaseStepManager, CookieSerializableStoreManager
from hereboxweb.schedule.reservation import calculate_storage_price, calculate_total_price, \
    ReservationSerializableFactory, RevisitOption, PeriodOption

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
                                             promotion=user_estimate.promotion)
                             )
    session['start_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template(template, active_menu='reservation')



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

    user_estimate = estimate_manager.get(request.cookies)
    if calculate_storage_price(user_estimate.regular_item_count, user_estimate.irregular_item_count,
                               user_estimate.period_option, user_estimate.period) <= 0:
        return bad_request(u'하나 이상의 상품을 구매하셔야 합니다.')

    order_helper = ReservationSerializableFactory.serializable('order')
    order_manager = PurchaseStepManager(order_helper, cookie_store_manager)
    user_order = order_manager.get(request.cookies)
    if user_order:
        return make_response(
            render_template(template, active_menu='reservation', old_phone_number=current_user.phone,
                            address1=user_order.address1,
                            address2=user_order.address2,
                            user_memo=user_order.user_memo))
    return make_response(
        render_template(template, active_menu='reservation', old_phone_number=current_user.phone))


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
    user_estimate = estimate_manager.get(request.cookies)
    if not user_estimate:
        return redirect(url_for('index'))

    start_time = escape(session.get('start_time'))
    if not start_time:
        return redirect(url_for('index'))

    order_helper = ReservationSerializableFactory.serializable('order')
    order_manager = PurchaseStepManager(order_helper, cookie_store_manager)
    user_order = order_manager.get(request.cookies)
    if not user_order:
        return redirect(url_for('index'))

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
                                             revisit_option=1 if user_order.revisit_option == RevisitOption.LATER else 0,
                                             revisit_date=user_order.revisit_date,
                                             revisit_time=revisit_time,
                                             user_memo=user_order.user_memo)
                             )
    response.set_cookie('totalPrice', '%d' % (total_price), path='/reservation/')
    return response


@schedule.route('/reservation/completion', methods=['GET'])
@mobile_template('{mobile/}completion.html')
@login_required
def completion(template):
    return render_template(template, active_menu='reservation')


@schedule.route('/delivery/order', methods=['GET', 'POST'])
@login_required
def delivery_order():
    if request.method == 'POST':
        return save_stuffs('/delivery/')

    packed_stuffs = get_stuffs()
    if not packed_stuffs or len(packed_stuffs) == 0:
        return redirect(url_for('index'))

    order_helper = DeliverySerializableFactory.serializable('order')
    cookie_store_manager = CookieSerializableStoreManager()
    order_manager = PurchaseStepManager(order_helper, cookie_store_manager)
    user_order = order_manager.get(request.cookies)
    if not user_order:
        session['start_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return make_response(
            render_template('delivery_reservation.html', active_menu='reservation',
                                                phone_number=current_user.phone))
    return make_response(
        render_template('delivery_reservation.html', active_menu='reservation',
                        phone_number=current_user.phone,
                        address1=user_order.address1,
                        address2=user_order.address2,
                        user_memo=user_order.user_memo))


@schedule.route('/delivery/review', methods=['GET', 'POST'])
@login_required
def delivery_review():
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
    user_order = cookie_store_manager.get(order_manager, request.cookies)
    if not user_order:
        return redirect(url_for('index'))

    visit_time = VisitTime.query.get(user_order.visit_time)
    total_price = calculate_total_delivery_price(packed_stuffs)
    response = make_response(render_template('delivery_review.html', active_menu='reservation',
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
def delivery_completion():
    return render_template('completion.html', active_menu='reservation')


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
    user_order = order_manager.get(request.cookies)
    if not user_order:
        return redirect(url_for('index'))

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
                                             revisit_option=1 if user_order.revisit_option == RevisitOption.LATER else 0,
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
    promotion_code = PromotionCode.query.join(Promotion).filter(PromotionCode.code == func.binary(code)).first()
    if not promotion_code:
        return bad_request(u'유효하지 않는 프로모션입니다.')

    today = datetime.datetime.now()
    if today > promotion_code.promotion.expired_at:
        return forbidden(u'유효 기간이 지난 프로모션입니다.')

    promotion_history = PromotionHistory.query.filter(PromotionHistory.code == promotion_code.id,
                                            PromotionHistory.user_id == current_user.uid).first()
    if promotion_history:
        return forbidden(u'이미 사용한 적이 있는 프로모션입니다.')

    response = jsonify(content = {'message': u'정상 처리되었습니다'})
    response.set_cookie('promotion', promotion_code.code, path='/reservation/')
    return response



