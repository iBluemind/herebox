# -*- coding: utf-8 -*-


from hereboxweb import database
from hereboxweb.utils import JsonSerializable


class VisitTime(database.Model, JsonSerializable):

    __tablename__ = 'visit_time'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    start_time = database.Column(database.Time)
    end_time = database.Column(database.Time)

    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        return '%s - %s' % (self.start_time.strftime('%H:%M'), self.end_time
                                                                .strftime('%H:%M'))
