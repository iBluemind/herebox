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

    database.create_all()

    database.session.add(VisitTime(start_time='10:00', end_time='12:00'))
    database.session.add(VisitTime(start_time='12:00', end_time='14:00'))
    database.session.add(VisitTime(start_time='14:00', end_time='16:00'))
    database.session.add(VisitTime(start_time='16:00', end_time='18:00'))
    database.session.add(VisitTime(start_time='18:00', end_time='20:00'))
    database.session.add(VisitTime(start_time='20:00', end_time='22:00'))
    database.session.add(User(email='contact@herebox.kr', name='구본준', status=UserStatus.ADMIN,
                              password='akswhddk8', phone='01064849686'))

    from hereboxweb.book.models import Box, BoxStatus, InStoreStatus
    for i in xrange(1, 10):
        database.session.add(Box(box_id='1A%03d' % i, in_store=InStoreStatus.IN_STORE,
                                                        status=BoxStatus.AVAILABLE))

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
    # a validator which makes a field required if
    # another field is set and has a truthy value

    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super(RequiredIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if bool(other_field.data):
            super(RequiredIf, self).__call__(form, field)
