# -*- coding: utf-8 -*-

import re

from flask.ext.compressor import FileAsset, CSSBundle, JSBundle
from sqlalchemy.sql import ClauseElement
from wtforms.validators import Required


class JsonSerializable(object):
    def to_json(inst, cls):
        d = {}
        for column in cls.__table__.columns:
            value = getattr(inst, column.name)

            import calendar, time, datetime
            if isinstance(value, datetime.datetime):
                if value.utcoffset() is not None:
                    value = value - value.utcoffset()

                value = int(
                    calendar.timegm(value.timetuple()) * 1000 +
                    value.microsecond / 1000
                )

            if isinstance(value, datetime.date):
                value = int(calendar.timegm(value.timetuple()) * 1000)

            d[column.name] = value
        return d


def is_none(attribute):
    return True if attribute is None or attribute == '' else False


def convert2escape_character(str):
    str = re.sub(r"([=\(\)|\-!@~\"&/\\\^\$\=])", r"\\\1", str)
    return re.escape(str)


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        params = dict((k, v) for k, v in kwargs.iteritems() if not isinstance(v, ClauseElement))
        if defaults:
            params.update(defaults)
        instance = model(**params)
        return instance


def initialize_db():
    from hereboxweb import database
    from hereboxweb.admin.models import VisitTime
    from hereboxweb.auth.models import User, UserStatus
    from hereboxweb.schedule.models import PromotionType, PromotionCode, Promotion

    # database.drop_all()
    database.create_all()

    database.session.add(VisitTime(start_time='10:00', end_time='12:00'))
    database.session.add(VisitTime(start_time='12:00', end_time='14:00'))
    database.session.add(VisitTime(start_time='14:00', end_time='16:00'))
    database.session.add(VisitTime(start_time='16:00', end_time='18:00'))
    database.session.add(VisitTime(start_time='18:00', end_time='20:00'))
    database.session.add(VisitTime(start_time='20:00', end_time='22:00'))
    database.session.add(User(email='contact@herebox.kr', name='구본준', status=UserStatus.ADMIN,
                              password='akswhddk8', phone='01064849686'))

    promotion = Promotion(u'첫 달 무료', u'첫달무료 10개 한정 프로모션', PromotionType.ALLOW_TO_ALL, '2016-05-31')
    database.session.add(promotion)

    from hereboxweb.book.models import Box, BoxStatus, InStoreStatus
    for i in xrange(1, 10):
        database.session.add(Box(box_id='1A%03d' % i, in_store=InStoreStatus.IN_STORE,
                                                        status=BoxStatus.AVAILABLE))

    database.session.commit()

    promotion_code = PromotionCode("HELLOHB", promotion.id)
    database.session.add(promotion_code)
    database.session.commit()


def staff_required(func):
    from functools import wraps
    from flask import current_app
    from flask.ext.login import current_user
    from hereboxweb.auth.models import UserStatus

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_app.login_manager._login_disabled:
            return func(*args, **kwargs)
        elif not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        else:
            if current_user.status < UserStatus.STAFF:
                return current_app.login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view


def add_months(src_date, months):
    import calendar
    import datetime

    month = src_date.month - 1 + months
    year = int(src_date.year + month / 12)
    month = month % 12 + 1
    day = min(src_date.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


class RequiredIf(Required):
    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super(RequiredIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if bool(other_field.data):
            super(RequiredIf, self).__call__(form, field)


def compress():
    from hereboxweb import compressor

    herebox_css = FileAsset(filename='assets/css/herebox.css', processors=['cssmin'])
    herebox_css_bundle = CSSBundle(
        name='herebox_css_bundle',
        assets=[
            herebox_css,
        ],
    )
    compressor.register_bundle(herebox_css_bundle)

    herebox_mobile_css = FileAsset(filename='assets/css/herebox_mobile.css', processors=['cssmin'])
    herebox_mobile_css_bundle = CSSBundle(
        name='herebox_mobile_css_bundle',
        assets=[
            herebox_mobile_css,
        ],
    )
    compressor.register_bundle(herebox_mobile_css_bundle)

    completion_js = FileAsset(filename='assets/js/completion.js', processors=['jsmin'])
    completion_js_bundle = JSBundle(
        name='completion_js_bundle',
        assets=[
            completion_js,
        ],
    )
    compressor.register_bundle(completion_js_bundle)

    delivery_payment_js = FileAsset(filename='assets/js/delivery_payment.js', processors=['jsmin'])
    delivery_payment_js_bundle = JSBundle(
        name='delivery_payment_js_bundle',
        assets=[
            delivery_payment_js,
        ],
    )
    compressor.register_bundle(delivery_payment_js_bundle)

    delivery_reservation_js = FileAsset(filename='assets/js/delivery_reservation.js', processors=['jsmin'])
    delivery_reservation_js_bundle = JSBundle(
        name='delivery_reservation_js_bundle',
        assets=[
            delivery_reservation_js,
        ],
    )
    compressor.register_bundle(delivery_reservation_js_bundle)

    delivery_review_js = FileAsset(filename='assets/js/delivery_review.js', processors=['jsmin'])
    delivery_review_js_bundle = JSBundle(
        name='delivery_review_js',
        assets=[
            delivery_review_js,
        ],
    )
    compressor.register_bundle(delivery_review_js_bundle)

    estimate_js = FileAsset(filename='assets/js/estimate.js', processors=['jsmin'])
    estimate_js_bundle = JSBundle(
        name='estimate_js_bundle',
        assets=[
            estimate_js,
        ],
    )
    compressor.register_bundle(estimate_js_bundle)

    extended_completion_js = FileAsset(filename='assets/js/extended_completion.js', processors=['jsmin'])
    extended_completion_js_bundle = JSBundle(
        name='extended_completion_js_bundle',
        assets=[
            extended_completion_js,
        ],
    )
    compressor.register_bundle(extended_completion_js_bundle)

    extended_estimate_js = FileAsset(filename='assets/js/extended_estimate.js', processors=['jsmin'])
    extended_estimate_js_bundle = JSBundle(
        name='extended_estimate_js_bundle',
        assets=[
            extended_estimate_js,
        ],
    )
    compressor.register_bundle(extended_estimate_js_bundle)

    extended_payment_js = FileAsset(filename='assets/js/extended_payment.js', processors=['jsmin'])
    extended_payment_js_bundle = JSBundle(
        name='extended_payment_js_bundle',
        assets=[
            extended_payment_js,
        ],
    )
    compressor.register_bundle(extended_payment_js_bundle)

    extended_review_js = FileAsset(filename='assets/js/extended_review.js', processors=['jsmin'])
    extended_review_js_bundle = JSBundle(
        name='extended_review_js_bundle',
        assets=[
            extended_review_js,
        ],
    )
    compressor.register_bundle(extended_review_js_bundle)

    hbcount_js = FileAsset(filename='assets/js/hbcount.js', processors=['jsmin'])
    hbcount_js_bundle = JSBundle(
        name='hbcount_js_bundle',
        assets=[
            hbcount_js,
        ],
    )
    compressor.register_bundle(hbcount_js_bundle)

    herebox_js = FileAsset(filename='assets/js/herebox.js', processors=['jsmin'])
    herebox_js_bundle = JSBundle(
        name='herebox_js_bundle',
        assets=[
            herebox_js,
        ],
    )
    compressor.register_bundle(herebox_js_bundle)

    introduce_js = FileAsset(filename='assets/js/introduce.js', processors=['jsmin'])
    introduce_js_bundle = JSBundle(
        name='introduce_js_bundle',
        assets=[
            introduce_js,
        ],
    )
    compressor.register_bundle(introduce_js_bundle)

    login_js = FileAsset(filename='assets/js/login.js', processors=['jsmin'])
    login_js_bundle = JSBundle(
        name='login_js_bundle',
        assets=[
            login_js,
        ],
    )
    compressor.register_bundle(login_js_bundle)

    my_info_js = FileAsset(filename='assets/js/my_info.js', processors=['jsmin'])
    my_info_js_bundle = JSBundle(
        name='my_info_js_bundle',
        assets=[
            my_info_js,
        ],
    )
    compressor.register_bundle(my_info_js_bundle)

    my_schedule_js = FileAsset(filename='assets/js/my_schedule.js', processors=['jsmin'])
    my_schedule_js_bundle = JSBundle(
        name='my_schedule_js_bundle',
        assets=[
            my_schedule_js,
        ],
    )
    compressor.register_bundle(my_schedule_js_bundle)

    my_stuff_js = FileAsset(filename='assets/js/my_stuff.js', processors=['jsmin'])
    my_stuff_js_bundle = JSBundle(
        name='my_stuff_js_bundle',
        assets=[
            my_stuff_js,
        ],
    )
    compressor.register_bundle(my_stuff_js_bundle)

    pickup_payment_js = FileAsset(filename='assets/js/pickup_payment.js', processors=['jsmin'])
    pickup_payment_js_bundle = JSBundle(
        name='pickup_payment_js_bundle',
        assets=[
            pickup_payment_js,
        ],
    )
    compressor.register_bundle(pickup_payment_js_bundle)

    pickup_reservation_js = FileAsset(filename='assets/js/pickup_reservation.js', processors=['jsmin'])
    pickup_reservation_js_bundle = JSBundle(
        name='pickup_reservation_js_bundle',
        assets=[
            pickup_reservation_js,
        ],
    )
    compressor.register_bundle(pickup_reservation_js_bundle)

    pickup_review_js = FileAsset(filename='assets/js/pickup_review.js', processors=['jsmin'])
    pickup_review_js_bundle = JSBundle(
        name='pickup_review_js_bundle',
        assets=[
            pickup_review_js,
        ],
    )
    compressor.register_bundle(pickup_review_js_bundle)

    reservation_js = FileAsset(filename='assets/js/reservation.js', processors=['jsmin'])
    reservation_js_bundle = JSBundle(
        name='reservation_js_bundle',
        assets=[
            reservation_js,
        ],
    )
    compressor.register_bundle(reservation_js_bundle)

    reservation_payment_js  = FileAsset(filename='assets/js/reservation_payment.js', processors=['jsmin'])
    reservation_payment_js_bundle = JSBundle(
        name='reservation_payment_js_bundle',
        assets=[
            reservation_payment_js,
        ],
    )
    compressor.register_bundle(reservation_payment_js_bundle)

    review_js = FileAsset(filename='assets/js/review.js', processors=['jsmin'])
    review_js_bundle = JSBundle(
        name='review_js_bundle',
        assets=[
            review_js,
        ],
    )
    compressor.register_bundle(review_js_bundle)

    signup_js = FileAsset(filename='assets/js/signup.js', processors=['jsmin'])
    signup_js_bundle = JSBundle(
        name='signup_js_bundle',
        assets=[
            signup_js,
        ],
    )
    compressor.register_bundle(signup_js_bundle)

    my_schedule_mobile_js = FileAsset(filename='assets/js/mobile/my_schedule.js', processors=['jsmin'])
    my_schedule_mobile_js_bundle = JSBundle(
        name='my_schedule_mobile_js_bundle',
        assets=[
            my_schedule_mobile_js,
        ],
    )
    compressor.register_bundle(my_schedule_mobile_js_bundle)


