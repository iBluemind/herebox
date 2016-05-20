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
from hereboxweb.schedule.delivery import save_delivery_order
from hereboxweb.schedule.models import *
from hereboxweb.schedule.reservation import save_order, get_estimate, save_estimate, calculate_storage_price,\
    get_order, calculate_total_price


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
    if request.method == 'POST':
        return save_order('reservation.html', '/reservation/')

    estimate_info = get_estimate()
    if not estimate_info:
        session['start_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return render_template(template, active_menu='reservation')

    return make_response(render_template(template, active_menu='reservation',
                                                 regular_item_count=estimate_info.get('regularItemNumberCount'),
                                                 irregular_item_count=estimate_info.get('irregularItemNumberCount'),
                                                 period=estimate_info.get('disposableNumberCount'),
                                                 period_option=estimate_info.get('optionsPeriod'),
                                                 binding_product0_count=estimate_info.get('bindingProduct0NumberCount'),
                                                 binding_product1_count=estimate_info.get('bindingProduct1NumberCount'),
                                                 binding_product2_count=estimate_info.get('bindingProduct2NumberCount'),
                                                 binding_product3_count=estimate_info.get('bindingProduct3NumberCount'),
                                                 promotion=estimate_info.get('inputPromotion'))
                                                )


@schedule.route('/reservation/order', methods=['GET', 'POST'])
@mobile_template('{mobile/}reservation.html')
@login_required
def order(template):
    if request.method == 'POST':
        return save_estimate()

    estimate_info = get_estimate()
    standard_box_count = estimate_info.get('regularItemNumberCount', 0)
    nonstandard_goods_count = estimate_info.get('irregularItemNumberCount', 0)
    period = estimate_info.get('disposableNumberCount', 0)
    peroid_option = estimate_info.get('optionsPeriod', 'disposable')

    if calculate_storage_price(standard_box_count, nonstandard_goods_count,
                               peroid_option, period) <= 0:
        return bad_request(u'하나 이상의 상품을 구매하셔야 합니다.')

    order_info = get_order()
    if order_info:
        return make_response(
            render_template(template, active_menu='reservation', old_phone_number=current_user.phone,
                            address1=order_info.get('inputAddress1'),
                            address2=order_info.get('inputAddress2'),
                            user_memo=order_info.get('textareaMemo')))
    return make_response(
        render_template(template, active_menu='reservation', old_phone_number=current_user.phone))


@schedule.route('/reservation/review', methods=['GET', 'POST'])
@mobile_template('{mobile/}review.html')
@login_required
def review(template):
    if request.method == 'POST':
        return save_order('reservation.html', '/reservation/')

    estimate_info = get_estimate()
    if not estimate_info:
        return redirect(url_for('index'))

    regular_item_count = estimate_info.get('regularItemNumberCount', 0)
    irregular_item_count = estimate_info.get('irregularItemNumberCount', 0)
    period = estimate_info.get('disposableNumberCount', 0)
    period_option = estimate_info.get('optionsPeriod', 'disposable')
    binding_product0_count = estimate_info.get('bindingProduct0NumberCount', 0)
    binding_product1_count = estimate_info.get('bindingProduct1NumberCount', 0)
    binding_product2_count = estimate_info.get('bindingProduct2NumberCount', 0)
    binding_product3_count = estimate_info.get('bindingProduct3NumberCount', 0)
    promotion = estimate_info.get('inputPromotion', None)
    start_time = escape(session.get('start_time'))

    if not start_time:
        return redirect(url_for('index'))

    order_info = get_order()
    if not order_info:
        return redirect(url_for('index'))

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
        return redirect(url_for('index'))

    visit_time = VisitTime.query.get(visit_time)
    if revisit_time:
        revisit_time = VisitTime.query.get(revisit_time)

    promotion_name = None
    promotion_code = PromotionCode.query.filter(PromotionCode.code == promotion).first()
    if promotion_code:
        promotion_name = promotion_code.promotion.name

    total_price = calculate_total_price(
        regular_item_count, irregular_item_count, period, period_option, promotion,
        binding_product0_count, binding_product1_count, binding_product2_count,
        binding_product3_count)

    response = make_response(render_template(template, active_menu='reservation',
                                                 standard_box_count=regular_item_count,
                                                 nonstandard_goods_count=irregular_item_count,
                                                 period_option=True if period_option == 'subscription' else False,
                                                 period=period,
                                                 binding_products={u'포장용 에어캡 1m': binding_product0_count,
                                                                   u'실리카겔 (제습제) 50g': binding_product1_count,
                                                                   u'압축팩 40cm x 60cm': binding_product2_count,
                                                                   u'테이프 48mm x 40m': binding_product3_count},
                                                 promotion=promotion_name,
                                                 total_price=u'{:,d}원'.format(total_price),
                                                 phone=phone_number,
                                                 address='%s %s' % (address1, address2),
                                                 visit_date=visit_date,
                                                 visit_time=visit_time,
                                                 revisit_option=1 if revisit_option == 'later' else 0,
                                                 revisit_date=revisit_date,
                                                 revisit_time=revisit_time,
                                                 user_memo=user_memo)
                                                )
    response.set_cookie('totalPrice', '%d' % (total_price), path='/reservation/')
    return response


@schedule.route('/reservation/completion', methods=['GET'])
@mobile_template('{mobile/}completion.html')
@login_required
def completion(template):
    return render_template(template, active_menu='reservation')


def calculate_total_delivery_price(packed_stuffs):
    return 2000 * len(packed_stuffs)


@schedule.route('/delivery/order', methods=['GET', 'POST'])
@login_required
def delivery_order():
    if request.method == 'POST':
        return save_stuffs('/delivery/')

    packed_stuffs = get_stuffs()
    if not packed_stuffs or len(packed_stuffs) == 0:
        return redirect(url_for('index'))

    order_info = get_order()
    if not order_info:
        session['start_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return make_response(
            render_template('delivery_reservation.html', active_menu='reservation',
                                                phone_number=current_user.phone))
    return make_response(
        render_template('delivery_reservation.html', active_menu='reservation',
                        phone_number=current_user.phone,
                        address1=order_info.get('inputAddress1'),
                        address2=order_info.get('inputAddress2'),
                        user_memo=order_info.get('textareaMemo')))


@schedule.route('/delivery/review', methods=['GET', 'POST'])
@login_required
def delivery_review():
    if request.method == 'POST':
        return save_delivery_order()

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

    visit_time = VisitTime.query.get(visit_time)
    response = make_response(render_template('delivery_review.html', active_menu='reservation',
                                             packed_stuffs=packed_stuffs,
                                             delivery_option=u'재보관 가능' if delivery_option == 'restore' else u'보관 종료',
                                             address=u'%s %s' % (address1, address2),
                                             phone_number=phone_number,
                                             visit_date_time=u'%s %s' % (visit_date, visit_time),
                                             user_memo=user_memo,
                                             total_price=u'{:,d}원'.format(calculate_total_delivery_price(packed_stuffs)))
                                            )
    response.set_cookie('totalPrice', '%d' % (calculate_total_delivery_price(packed_stuffs)), path='/delivery/')
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

    order_info = get_order()
    if not order_info:
        session['start_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return make_response(
            render_template('pickup_reservation.html', active_menu='reservation',
                                                phone_number=current_user.phone))
    return make_response(
        render_template('pickup_reservation.html', active_menu='reservation',
                        phone_number=current_user.phone,
                        address1=order_info.get('inputAddress1'),
                        address2=order_info.get('inputAddress2'),
                        user_memo=order_info.get('textareaMemo')))


@schedule.route('/pickup/review', methods=['GET', 'POST'])
@login_required
def pickup_review():
    if request.method == 'POST':
        return save_order('pickup_reservation.html', '/pickup/')

    packed_stuffs = get_stuffs()
    if not packed_stuffs or len(packed_stuffs) == 0:
        return redirect(url_for('index'))

    order_info = get_order()
    if not order_info:
        return redirect(url_for('index'))

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

    visit_time = VisitTime.query.get(visit_time)
    response = make_response(render_template('pickup_review.html', active_menu='reservation',
                                             packed_stuffs=packed_stuffs,
                                             phone_number=phone_number,
                                             address=u'%s %s' % (address1, address2),
                                             visit_date_time=u'%s %s' % (visit_date, visit_time),
                                             revisit_option=1 if revisit_option == 'later' else 0,
                                             revisit_date_time=u'%s %s' % (revisit_date, revisit_time),
                                             user_memo=user_memo,
                                             total_price=u'{:,d}원'.format(calculate_total_delivery_price(packed_stuffs)))
                                            )
    response.set_cookie('totalPrice', '%d' % (calculate_total_delivery_price(packed_stuffs)), path='/pickup/')
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



