# -*- coding: utf-8 -*-


from hereboxweb import database
from hereboxweb.utils import JsonSerializable


class AlertNewArea(database.Model, JsonSerializable):

    __tablename__ = 'alert_new_area'

    id = database.Column(database.Integer, primary_key=True, autoincrement=True)
    area = database.Column(database.String(30))
    contact = database.Column(database.String(30))

    def __init__(self, area, contact):
        self.area = area
        self.contact = contact