# -*- coding: utf-8 -*-

import json
from flask import request, render_template, redirect, url_for
from flask_login import login_required, current_user
from flask_mobility.decorators import mobile_template
from sqlalchemy import func
from hereboxweb import response_template, bad_request, forbidden
from hereboxweb.admin.models import VisitTime
from hereboxweb.auth.models import User
from hereboxweb.book.models import Goods
from hereboxweb.book.stuffs import get_goods
from hereboxweb.book.views import get_stuffs
from hereboxweb.payment import payment
from hereboxweb.payment.models import *
from hereboxweb.schedule.delivery import calculate_total_delivery_price, DeliverySerializableFactory, DeliveryOption
from hereboxweb.schedule.models import NewReservation, ReservationStatus, Schedule, \
    ScheduleStatus, ScheduleType, ReservationRevisitType, DeliveryReservation, RestoreReservation, PromotionCode, \
    PromotionHistory, Promotion, ExtendPeriod, ExtendPeriodStatus
from hereboxweb.schedule.price import IRREGULAR_ITEM_PRICE, REGULAR_ITEM_PRICE, calculate_total_price
from hereboxweb.schedule.purchase_step import CookieSerializableStoreManager, PurchaseStepManager
from hereboxweb.schedule.reservation import ReservationSerializableFactory, PeriodOption, \
    RevisitOption
from hereboxweb.tasks import send_mail
from hereboxweb.utils import add_months


pay_types = {
    'visit': PayType.DIRECT,
    'card': PayType.CARD,
    'phone': PayType.PHONE,
    'kakao': PayType.KAKAOPAY,
    'account': PayType.ACCOUNT,
}


@payment.route('/pickup/payment', methods=['GET', 'POST'])
@login_required
def pickup_payment():
    packed_stuffs = get_stuffs()
    if not packed_stuffs or len(packed_stuffs) == 0:
        if request.method == 'POST':
            return bad_request()
        return redirect(url_for('index'))

    order_helper = ReservationSerializableFactory.serializable('order')
    cookie_store_manager = CookieSerializableStoreManager()
    order_manager = PurchaseStepManager(order_helper, cookie_store_manager)
    try:
        user_order = order_manager.get(request.cookies)
        if not user_order:
            if request.method == 'POST':
                return bad_request()
            return redirect(url_for('index'))
    except KeyError as error:
        return bad_request(error.message)
    except ValueError:
        return bad_request()

    user_total_price = int(request.cookies.get('totalPrice'))
    total_price = calculate_total_delivery_price(packed_stuffs)

    if user_total_price != total_price:
        if request.method == 'POST':
            return bad_request()
        return redirect(url_for('schedule.estimate'))

    if request.method == 'POST':
        user_pay_type = request.form.get('optionsPayType')

        purchase = Purchase(
            status=PurchaseStatus.NORMAL,
            amount=total_price,
            pay_type=pay_types[user_pay_type],
            user_id=current_user.uid
        )

        database.session.add(purchase)

        goods = get_goods()
        restore_reservation = RestoreReservation(
            status=ReservationStatus.WAITING,
            user_id=current_user.uid,
            contact=user_order.phone_number,
            address='%s %s' % (user_order.address1, user_order.address2),
            delivery_date=user_order.visit_date,
            delivery_time=user_order.visit_time,
            recovery_date=user_order.revisit_date,
            recovery_time=user_order.revisit_time,
            revisit_option=ReservationRevisitType.LATER if user_order.revisit_option == RevisitOption.LATER else ReservationRevisitType.IMMEDIATE,
            user_memo=user_order.user_memo,
            pay_type=pay_types[user_pay_type],
            goods=goods,
            purchase_id=purchase.id
        )
        database.session.add(restore_reservation)

        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', 500)

        new_visit_schedule = Schedule(status=ScheduleStatus.WAITING,
                                      schedule_type=ScheduleType.RESTORE_DELIVERY,
                                      staff_id=1,
                                      customer_id=current_user.uid,
                                      schedule_date=user_order.visit_date,
                                      schedule_time_id=user_order.visit_time,
                                      reservation_id=restore_reservation.id)
        database.session.add(new_visit_schedule)

        new_revisit_schedule = None
        if user_order.revisit_option == RevisitOption.LATER:
            new_revisit_schedule = Schedule(status=ScheduleStatus.WAITING,
                                            schedule_type=ScheduleType.RESTORE_RECOVERY,
                                            staff_id=1,
                                            customer_id=current_user.uid,
                                            schedule_date=user_order.revisit_date,
                                            schedule_time_id=user_order.revisit_time,
                                            reservation_id=restore_reservation.id)
        if new_revisit_schedule:
            database.session.add(new_revisit_schedule)

        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', 500)

        visit_time = VisitTime.query.get(user_order.visit_time)
        pay_type = u'현장' if restore_reservation.pay_type == PayType.DIRECT else u'온라인'

        parsed_goods_ids = ''
        for single_goods in goods:
            parsed_goods_ids += '%s ' % single_goods.goods_id

        mail_msg_body = u"""
            재보관 주문 정보입니다.
            http://www.herebox.kr/admin/reservation/%s

            스케줄번호: %s   회원: %s
            주소: %s   연락처: %s
            지불방법: %s

            방문일자: %s   방문시간: %s
            대상물품: %s   남긴말: %s
            """ % (
            restore_reservation.reservation_id, new_visit_schedule.schedule_id,
            current_user.name, restore_reservation.address, current_user.phone,
            pay_type, user_order.visit_date, visit_time,
            parsed_goods_ids, restore_reservation.user_memo
        )

        send_mail.apply_async(args=[u'재보관 주문 정보: %s' % new_visit_schedule.schedule_id,
                                    mail_msg_body, 'contact@herebox.kr'])

        if new_revisit_schedule:
            revisit_time = VisitTime.query.get(user_order.revisit_time)

            mail_msg_body = u"""
                [재방문] 재보관 주문 정보입니다.
                http://www.herebox.kr/admin/reservation/%s

                스케줄번호: %s   회원: %s
                주소: %s   연락처: %s
                지불방법: %s

                방문일자: %s   방문시간: %s
                대상물품: %s   남긴말: %s
                """ % (
                restore_reservation.reservation_id, new_visit_schedule.schedule_id,
                current_user.name, restore_reservation.address, current_user.phone,
                pay_type, user_order.revisit_date, revisit_time,
                parsed_goods_ids, restore_reservation.user_memo
            )

            send_mail.apply_async(args=[u'[재방문] 재보관 주문 정보: %s' % new_revisit_schedule.schedule_id,
                                        mail_msg_body, 'contact@herebox.kr'])

        return response_template(u'정상 처리되었습니다', 200)
    return render_template('pickup_payment.html', active_menu='reservation')


@payment.route('/delivery/payment', methods=['GET', 'POST'])
@login_required
@mobile_template('{mobile/}delivery_payment.html')
def delivery_payment(template):
    packed_stuffs = get_stuffs()
    if not packed_stuffs or len(packed_stuffs) == 0:
        if request.method == 'POST':
            return bad_request()
        return redirect(url_for('index'))

    order_helper = DeliverySerializableFactory.serializable('order')
    cookie_store_manager = CookieSerializableStoreManager()
    order_manager = PurchaseStepManager(order_helper, cookie_store_manager)
    try:
        user_order = order_manager.get(request.cookies)
        if not user_order:
            if request.method == 'POST':
                return bad_request()
            return redirect(url_for('index'))
    except KeyError as error:
        return bad_request(error.message)
    except ValueError:
        return bad_request()

    user_total_price = int(request.cookies.get('totalPrice'))
    total_price = calculate_total_delivery_price(packed_stuffs)

    if user_total_price != total_price:
        if request.method == 'POST':
            return bad_request()
        return redirect(url_for('schedule.estimate'))

    if request.method == 'POST':
        user_pay_type = request.form.get('optionsPayType')

        purchase = Purchase(
            status=PurchaseStatus.NORMAL,
            amount=total_price,
            pay_type=pay_types[user_pay_type],
            user_id=current_user.uid
        )

        database.session.add(purchase)

        goods = get_goods()
        delivery_reservation = DeliveryReservation(
            status=ReservationStatus.WAITING,
            user_id=current_user.uid,
            contact=user_order.phone_number,
            address='%s %s' % (user_order.address1, user_order.address2),
            delivery_option=True if user_order.delivery_option == DeliveryOption.EXPIRE else False,
            delivery_date=user_order.visit_date,
            delivery_time=user_order.visit_time,
            user_memo=user_order.user_memo,
            pay_type=pay_types[user_pay_type],
            goods=goods,
            purchase_id=purchase.id
        )
        database.session.add(delivery_reservation)

        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', 500)

        new_visit_schedule = Schedule(status=ScheduleStatus.WAITING,
                                      schedule_type=ScheduleType.DELIVERY,
                                      staff_id=1,
                                      customer_id=current_user.uid,
                                      schedule_date=user_order.visit_date,
                                      schedule_time_id=user_order.visit_time,
                                      reservation_id=delivery_reservation.id)
        database.session.add(new_visit_schedule)


        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', 500)

        visit_time = VisitTime.query.get(user_order.visit_time)
        pay_type = u'현장' if delivery_reservation.pay_type == PayType.DIRECT else u'온라인'
        delivery_option = u'만료' if user_order.delivery_option == DeliveryOption.EXPIRE else u'유지'
        parsed_goods_ids = ''
        for single_goods in goods:
            parsed_goods_ids += '%s ' % single_goods.goods_id

        mail_msg_body = u"""
            배송 주문 정보입니다.
            http://www.herebox.kr/admin/reservation/%s

            스케줄번호: %s   회원: %s
            주소: %s   연락처: %s
            지불방법: %s

            방문일자: %s   방문시간: %s
            대상물품: %s   배송옵션: %s
            남긴말: %s
            """ % (
            delivery_reservation.reservation_id, new_visit_schedule.schedule_id,
            current_user.name, delivery_reservation.address, current_user.phone,
            pay_type, user_order.visit_date, visit_time,
            parsed_goods_ids, delivery_option, delivery_reservation.user_memo
        )

        send_mail.apply_async(args=[u'배송 주문 정보: %s' % new_visit_schedule.schedule_id,
                                    mail_msg_body, 'contact@herebox.kr'])

        return response_template(u'정상 처리되었습니다', 200)
    return render_template(template, active_menu='reservation')


@payment.route('/extended/payment', methods=['GET', 'POST'])
@login_required
def extended_payment():
    def calculate_total_price():
        total_price = 0
        for goods_id in estimate_info.keys():
            if type(estimate_info[goods_id]) is int:
                if goods_id.startswith('B'):
                    total_price += (IRREGULAR_ITEM_PRICE * estimate_info[goods_id])
                else:
                    total_price += (REGULAR_ITEM_PRICE * estimate_info[goods_id])
            else:
                del estimate_info[goods_id]
        return total_price

    estimate_info = request.cookies.get('estimate')
    order_info = request.cookies.get('order')

    if not estimate_info or not order_info:
        if request.method == 'POST':
            return response_template(u'잘못된 요청입니다.', status=400)
        return redirect(url_for('book.my_stuff'))

    estimate_info = json.loads(estimate_info)
    order_info = json.loads(order_info)
    start_time = order_info.get('start_time')
    user_total_price = order_info.get('total_price')

    if not start_time or not user_total_price:
        if request.method == 'POST':
            return response_template(u'잘못된 요청입니다.', status=400)
        return redirect(url_for('book.my_stuff'))

    try:
        datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        user_total_price = int(user_total_price)
    except:
        if request.method == 'POST':
            return response_template(u'잘못된 요청입니다.', status=400)
        return redirect(url_for('book.my_stuff'))

    total_price = calculate_total_price()
    if user_total_price != total_price:
        if request.method == 'POST':
            return response_template(u'잘못된 요청입니다.', status=400)
        return redirect(url_for('book.my_stuff'))

    if request.method == 'POST':
        user_pay_type = request.form.get('optionsPayType')

        stuffs = Goods.query.filter(
            Goods.goods_id.in_(estimate_info.keys())
        ).limit(10).all()

        for item in stuffs:
            new_extend_period = None
            if pay_types[user_pay_type] is PayType.ACCOUNT:
                new_extend_period = ExtendPeriod(estimate_info[item.goods_id],
                                                 item.id, ExtendPeriodStatus.WAITING)
            else:
                #TODO: PG사 API로부터 결제 성공 여부 확인 후 아래 작업을 수행하도록 추가 구현해야 함.
                new_extend_period = ExtendPeriod(estimate_info[item.goods_id],
                                                 item.id, ExtendPeriodStatus.ACCEPTED)
                item.expired_at = add_months(item.expired_at, estimate_info[item.goods_id])

            if new_extend_period:
                database.session.add(new_extend_period)

        # 무통장 입금 처리는 어드민에서 연장 버튼 누를 시 자동 처리
        if pay_types[user_pay_type] is not PayType.ACCOUNT:
            purchase = Purchase(
                status=PurchaseStatus.NORMAL,
                amount=total_price,
                pay_type=pay_types[user_pay_type],
                user_id=current_user.uid
            )
            database.session.add(purchase)

        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', status=500)
        return response_template(u'정상 처리되었습니다', status=200)
    return render_template('extended_payment.html', active_menu='reservation')


@payment.route('/reservation/payment', methods=['GET', 'POST'])
@mobile_template('{mobile/}reservation_payment.html')
@login_required
def reservation_payment(template):
    cookie_store_manager = CookieSerializableStoreManager()
    estimate_helper = ReservationSerializableFactory.serializable('estimate')
    estimate_manager = PurchaseStepManager(estimate_helper, cookie_store_manager)

    try:
        user_estimate = estimate_manager.get(request.cookies)
    except KeyError as error:
        return bad_request(error.message)
    except ValueError:
        return bad_request()

    total_price = calculate_total_price(
        user_estimate.regular_item_count, user_estimate.irregular_item_count,
        user_estimate.period, user_estimate.period_option, user_estimate.promotion,
        user_estimate.binding_product0_count, user_estimate.binding_product1_count,
        user_estimate.binding_product2_count, user_estimate.binding_product3_count
    )

    user_total_price = int(request.cookies.get('totalPrice'))
    if user_total_price != total_price:
        if request.method == 'POST':
            return bad_request()
        return redirect(url_for('schedule.estimate'))

    if request.method == 'POST':
        order_helper = ReservationSerializableFactory.serializable('order')
        order_manager = PurchaseStepManager(order_helper, cookie_store_manager)

        try:
            user_order = order_manager.get(request.cookies)
        except KeyError as error:
            return bad_request(error.message)
        except ValueError:
            return bad_request()

        user_pay_type = request.form.get('optionsPayType')

        if len(user_estimate.promotion) > 0:
            promotion_code = PromotionCode.query.join(Promotion).filter(
                                PromotionCode.code == func.binary(user_estimate.promotion)).first()
            if not promotion_code:
                return bad_request(u'유효하지 않는 프로모션입니다.')

            today = datetime.datetime.now()
            if today > promotion_code.promotion.expired_at:
                return forbidden(u'유효 기간이 지난 프로모션입니다.')

            promotion_history = PromotionHistory.query.filter(PromotionHistory.code == promotion_code.id,
                                                              PromotionHistory.user_id == current_user.uid).first()
            if promotion_history:
                return forbidden(u'이미 사용한 적이 있는 프로모션입니다.')

        purchase = Purchase(
            status=PurchaseStatus.NORMAL,
            amount=total_price,
            pay_type=pay_types[user_pay_type],
            user_id=current_user.uid
        )
        database.session.add(purchase)

        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', 500)

        promotion_id = None
        if user_estimate.promotion:
            promotion_code = PromotionCode.query.join(Promotion).filter(PromotionCode.code == user_estimate.promotion).first()
            if promotion_code:
                promotion_id = promotion_code.promotion.id
                promotion_history = PromotionHistory(current_user.uid, promotion_code.id)
                database.session.add(promotion_history)
                try:
                    database.session.commit()
                except:
                    return response_template(u'문제가 발생했습니다.', status=500)

        new_reservation = NewReservation(
            status=ReservationStatus.WAITING,
            standard_box_count=user_estimate.regular_item_count,
            nonstandard_goods_count=user_estimate.irregular_item_count,
            period=user_estimate.period,
            promotion=user_estimate.promotion,
            fixed_rate=True if user_estimate.period_option == PeriodOption.SUBSCRIPTION else False,
            binding_products={u'포장용 에어캡 1m': user_estimate.binding_product0_count, u'실리카겔 (제습제) 50g': user_estimate.binding_product1_count,
                              u'압축팩 40cm x 60cm': user_estimate.binding_product2_count, u'테이프 48mm x 40m': user_estimate.binding_product3_count},
            contact=user_order.phone_number,
            address='%s %s' % (user_order.address1, user_order.address2),
            delivery_date=user_order.visit_date,
            delivery_time=user_order.visit_time,
            recovery_date=user_order.revisit_date,
            recovery_time=user_order.revisit_time,
            revisit_option=ReservationRevisitType.LATER if user_order.revisit_option == RevisitOption.LATER else ReservationRevisitType.IMMEDIATE,
            user_memo=user_order.user_memo,
            pay_type=pay_types[user_pay_type],
            user_id=current_user.uid,
            purchase_id=purchase.id,
            promotion_id=promotion_id
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
                                      schedule_date=user_order.visit_date,
                                      schedule_time_id=user_order.visit_time,
                                      reservation_id=new_reservation.id)
        database.session.add(new_visit_schedule)

        new_revisit_schedule = None
        if user_order.revisit_option == RevisitOption.LATER:
            new_revisit_schedule = Schedule(status=ScheduleStatus.WAITING,
                                            schedule_type=ScheduleType.PICKUP_RECOVERY,
                                            staff_id=1,
                                            customer_id=current_user.uid,
                                            schedule_date=user_order.revisit_date,
                                            schedule_time_id=user_order.revisit_time,
                                            reservation_id=new_reservation.id)
        if new_revisit_schedule:
            database.session.add(new_revisit_schedule)

        logged_in_user = User.query.get(current_user.uid)
        logged_in_user.phone = user_order.phone_number
        logged_in_user.address1 = user_order.address1
        logged_in_user.address2 = user_order.address2

        try:
            database.session.commit()
        except:
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요.', 500)

        visit_time = VisitTime.query.get(user_order.visit_time)
        pay_type = u'현장' if new_reservation.pay_type == PayType.DIRECT else u'온라인'

        parsed_binding_products = ''
        binding_products = json.loads(new_reservation.binding_products)
        for key in binding_products.keys():
            parsed_binding_products += '%s: ' % key
            parsed_binding_products += '%s ' % binding_products[key]

        mail_msg_body = u"""
        신규 주문 정보입니다.
        http://www.herebox.kr/admin/reservation/%s

        스케줄번호: %s   회원: %s
        주소: %s   연락처: %s
        지불방법: %s

        방문일자: %s   방문시간: %s
        규격물품: %s   비규격물품: %s
        포장용품: %s   기간: %s
        남긴말: %s
        """ % (
            new_reservation.reservation_id, new_visit_schedule.schedule_id,
            current_user.name, new_reservation.address, current_user.phone,
            pay_type, user_order.visit_date, visit_time,
            new_reservation.standard_box_count,
            new_reservation.nonstandard_goods_count, parsed_binding_products,
            new_reservation.period, new_reservation.user_memo
        )

        send_mail.apply_async(args=[u'신규 주문 정보: %s' % new_visit_schedule.schedule_id,
                                    mail_msg_body, 'contact@herebox.kr'])

        if new_revisit_schedule:
            revisit_time = VisitTime.query.get(user_order.revisit_time)

            mail_msg_body = u"""
                [재방문] 신규 주문 정보입니다.
                http://www.herebox.kr/admin/reservation/%s

                스케줄번호: %s   회원: %s
                주소: %s   연락처: %s
                지불방법: %s

                방문일자: %s   방문시간: %s
                규격물품: %s   비규격물품: %s
                포장용품: %s   기간: %s
                남긴말: %s
                """ % (
                new_reservation.reservation_id, new_visit_schedule.schedule_id,
                current_user.name, new_reservation.address, current_user.phone,
                pay_type, user_order.revisit_date, revisit_time,
                new_reservation.standard_box_count,
                new_reservation.nonstandard_goods_count, parsed_binding_products,
                new_reservation.period, new_reservation.user_memo
            )

            send_mail.apply_async(args=[u'[재방문] 신규 주문 정보: %s' % new_revisit_schedule.schedule_id,
                                    mail_msg_body, 'contact@herebox.kr'])

        return response_template(u'정상 처리되었습니다', 200)
    return render_template(template, active_menu='reservation')

