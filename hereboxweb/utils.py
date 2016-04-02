# -*- coding: utf-8 -*-
import re


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

