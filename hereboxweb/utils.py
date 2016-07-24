# -*- coding: utf-8 -*-

import re
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

    # database.session.add(VisitTime(start_time='10:00', end_time='12:00'))
    # database.session.add(VisitTime(start_time='12:00', end_time='14:00'))
    # database.session.add(VisitTime(start_time='14:00', end_time='16:00'))
    # database.session.add(VisitTime(start_time='16:00', end_time='18:00'))
    # database.session.add(VisitTime(start_time='18:00', end_time='20:00'))
    # database.session.add(VisitTime(start_time='20:00', end_time='22:00'))
    # database.session.add(User(email='contact@herebox.kr', name='구본준', status=UserStatus.ADMIN,
    #                           password='akswhddk8', phone='01064849686'))
    #
    # promotion = Promotion(u'첫 달 무료', u'첫달무료 10개 한정 프로모션', PromotionType.ALLOW_TO_ALL, '2016-05-31')
    # database.session.add(promotion)
    #
    # from hereboxweb.book.models import Box, BoxStatus, InStoreStatus
    # for i in xrange(1, 10):
    #     database.session.add(Box(box_id='1A%03d' % i, in_store=InStoreStatus.IN_STORE,
    #                                                     status=BoxStatus.AVAILABLE))
    #
    # database.session.commit()
    #
    # promotion_code = PromotionCode("HELLOHB", promotion.id)
    # database.session.add(promotion_code)
    # database.session.commit()


def staff_required(func):
    from functools import wraps
    from flask import current_app
    from flask.ext.login import current_user
    from hereboxweb.auth.models import UserStatus

    @wraps(func)
    def decorated_view(*args, **kwargs):
        from flask import redirect, url_for
        if current_app.login_manager._login_disabled:
            return func(*args, **kwargs)
        elif not current_user.is_authenticated:
            return redirect(url_for('admin.admin_login'))
        else:
            if current_user.status < UserStatus.STAFF:
                return redirect(url_for('admin.admin_login'))
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
    from flask.ext.assets import Bundle
    from hereboxweb import assets

    herebox_css = Bundle('assets/css/herebox.css', filters='cssmin', output='gen/herebox.min.css')
    assets.register('herebox_css', herebox_css)
    herebox_mobile_css = Bundle('assets/css/herebox_mobile.css', filters='cssmin', output='gen/herebox_mobile.min.css')
    assets.register('herebox_mobile_css', herebox_mobile_css)

    completion_js = Bundle('assets/js/completion.js', filters='jsmin', output='gen/completion.min.js')
    assets.register('completion_js', completion_js)
    delivery_payment_js = Bundle('assets/js/delivery_payment.js', filters='jsmin', output='gen/delivery_payment.min.js')
    assets.register('delivery_payment_js', delivery_payment_js)
    delivery_reservation_js = Bundle('assets/js/delivery_reservation.js', filters='jsmin', output='gen/delivery_reservation.min.js')
    assets.register('delivery_reservation_js', delivery_reservation_js)
    delivery_review_js = Bundle('assets/js/delivery_review.js', filters='jsmin', output='gen/delivery_review.min.js')
    assets.register('delivery_review_js', delivery_review_js)
    estimate_js = Bundle('assets/js/estimate.js', filters='jsmin', output='gen/estimate.min.js')
    assets.register('estimate_js', estimate_js)
    extended_completion_js = Bundle('assets/js/extended_completion.js', filters='jsmin', output='gen/extended_completion.min.js')
    assets.register('extended_completion_js', extended_completion_js)
    extended_estimate_js = Bundle('assets/js/extended_estimate.js', filters='jsmin', output='gen/extended_estimate.min.js')
    assets.register('extended_estimate_js', extended_estimate_js)
    extended_payment_js = Bundle('assets/js/extended_payment.js', filters='jsmin', output='gen/extended_payment.min.js')
    assets.register('extended_payment_js', extended_payment_js)
    extended_review_js = Bundle('assets/js/extended_review.js', filters='jsmin', output='gen/extended_review.min.js')
    assets.register('extended_review_js', extended_review_js)
    hbcounter_js = Bundle('assets/js/hbcounter.js', filters='jsmin', output='gen/hbcounter.min.js')
    assets.register('hbcounter_js', hbcounter_js)
    herebox_js = Bundle('assets/js/herebox.js', filters='jsmin', output='gen/herebox.min.js')
    assets.register('herebox_js', herebox_js)
    introduce_js = Bundle('assets/js/introduce.js', filters='jsmin', output='gen/introduce.min.js')
    assets.register('introduce_js', introduce_js)
    login_js = Bundle('assets/js/login.js', filters='jsmin', output='gen/login.min.js')
    assets.register('login_js', login_js)
    my_info_js = Bundle('assets/js/my_info.js', filters='jsmin', output='gen/my_info.min.js')
    assets.register('my_info_js', my_info_js)
    my_schedule_js = Bundle('assets/js/my_schedule.js', filters='jsmin', output='gen/my_schedule.min.js')
    assets.register('my_schedule_js', my_schedule_js)
    my_stuff_js = Bundle('assets/js/my_stuff.js', filters='jsmin', output='gen/my_stuff.min.js')
    assets.register('my_stuff_js', my_stuff_js)
    pickup_payment_js = Bundle('assets/js/pickup_payment.js', filters='jsmin', output='gen/pickup_payment.min.js')
    assets.register('pickup_payment_js', pickup_payment_js)
    pickup_reservation_js = Bundle('assets/js/pickup_reservation.js', filters='jsmin', output='gen/pickup_reservation.min.js')
    assets.register('pickup_reservation_js', pickup_reservation_js)
    pickup_review_js = Bundle('assets/js/pickup_review.js', filters='jsmin', output='gen/pickup_review.min.js')
    assets.register('pickup_review_js', pickup_review_js)
    reservation_js = Bundle('assets/js/reservation.js', filters='jsmin', output='gen/reservation.min.js')
    assets.register('reservation_js', reservation_js)
    reservation_payment_js = Bundle('assets/js/reservation_payment.js', filters='jsmin', output='gen/reservation_payment.min.js')
    assets.register('reservation_payment_js', reservation_payment_js)
    review_js = Bundle('assets/js/review.js', filters='jsmin', output='gen/review.min.js')
    assets.register('review_js', review_js)
    signup_js = Bundle('assets/js/signup.js', filters='jsmin', output='gen/signup.min.js')
    assets.register('signup_js', signup_js)
    my_schedule_mobile_js = Bundle('assets/js/mobile/my_schedule.js', filters='jsmin', output='gen/my_schedule_mobile.min.js')
    assets.register('my_schedule_mobile_js', my_schedule_mobile_js)
    find_pw_js = Bundle('assets/js/find_pw.js', filters='jsmin',
                                   output='gen/find_pw.min.js')
    assets.register('find_pw_js', find_pw_js)


def build_compressed_assets():
    import logging
    log = logging.getLogger('webassets')
    log.addHandler(logging.StreamHandler())
    log.setLevel(logging.DEBUG)

    from webassets.script import CommandLineEnvironment
    from hereboxweb import assets
    cmdenv = CommandLineEnvironment(assets, log)
    cmdenv.build()


def upload_to_s3():
    from flask.ext.s3 import create_all
    from hereboxweb import app
    create_all(app)


