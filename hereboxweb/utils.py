# -*- coding: utf-8 -*-


import re

from sqlalchemy.sql import ClauseElement

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

    database.drop_all()
    database.create_all()

    database.session.add(VisitTime(start_time='10:00', end_time='12:00'))
    database.session.add(VisitTime(start_time='12:00', end_time='14:00'))
    database.session.add(VisitTime(start_time='14:00', end_time='16:00'))
    database.session.add(VisitTime(start_time='16:00', end_time='18:00'))
    database.session.add(VisitTime(start_time='18:00', end_time='20:00'))
    database.session.add(VisitTime(start_time='20:00', end_time='22:00'))
    database.session.add(User(email='contact@herebox.kr', name='구본준', status=UserStatus.ADMIN,
                              password='akswhddk8', phone='01064849686'))

    database.session.commit()
