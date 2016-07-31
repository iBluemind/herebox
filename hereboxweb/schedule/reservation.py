# -*- coding: utf-8 -*-


import datetime
import re
from flask import escape, session
from flask_login import current_user
from hereboxweb.schedule.purchase_step import UserInputSerializable, UserInputSerializableFactory


class PeriodOption(object):
    DISPOSABLE = 'disposable'
    SUBSCRIPTION = 'subscription'


class RevisitOption(object):
    IMMEDIATE = 'immediate'
    LATER = 'later'


class ReservationEstimate(UserInputSerializable):

    __user_input_type__ = 'estimate'

    def user_input_keys(self):
        return ['regularItemNumberCount', 'irregularItemNumberCount', 'disposableNumberCount',
         'optionsPeriod', 'bindingProduct0NumberCount', 'bindingProduct1NumberCount',
         'bindingProduct2NumberCount', 'bindingProduct3NumberCount', 'inputPromotion']

    def deserialize(self, user_input):
        self.regular_item_count = int(user_input.get(self.user_input_keys()[0], 0))
        self.irregular_item_count = int(user_input.get(self.user_input_keys()[1], 0))
        self.period_option = user_input.get(self.user_input_keys()[3], PeriodOption.DISPOSABLE)
        if self.period_option == PeriodOption.DISPOSABLE:
            self.period = int(user_input.get(self.user_input_keys()[2], 0))
        self.binding_product0_count = int(user_input.get(self.user_input_keys()[4], 0))
        self.binding_product1_count = int(user_input.get(self.user_input_keys()[5], 0))
        self.binding_product2_count = int(user_input.get(self.user_input_keys()[6], 0))
        self.binding_product3_count = int(user_input.get(self.user_input_keys()[7], 0))
        self.promotion = user_input.get(self.user_input_keys()[8], None)

    def serialize(self):
        return {
            'regularItemNumberCount': self.regular_item_count or 0,
            'irregularItemNumberCount': self.irregular_item_count or 0,
            'optionsPeriod': self.period_option,
            'bindingProduct0NumberCount': self.binding_product0_count or 0,
            'bindingProduct1NumberCount': self.binding_product1_count or 0,
            'bindingProduct2NumberCount': self.binding_product2_count or 0,
            'bindingProduct3NumberCount': self.binding_product3_count or 0,
            'disposableNumberCount': self.period or 0,
            'inputPromotion': self.promotion,
        }


class ReservationOrder(UserInputSerializable):

    __user_input_type__ = 'order'

    def user_input_keys(self):
        return ['optionsRevisit', 'inputPhoneNumber', 'inputVisitDate',
         'inputPostCode', 'inputVisitTime', 'inputAddress1',
         'inputAddress2', 'inputRevisitTime', 'inputRevisitDate', 'textareaMemo']

    def deserialize(self, user_input):
        self.revisit_option = user_input.get(self.user_input_keys()[0], RevisitOption.IMMEDIATE)
        self.phone_number = user_input.get(self.user_input_keys()[1], None)
        self.visit_date = user_input.get(self.user_input_keys()[2], PeriodOption.DISPOSABLE)
        self.post_code = user_input.get(self.user_input_keys()[3], None)
        self.visit_time = int(user_input.get(self.user_input_keys()[4], 0))
        self.address1 = user_input.get(self.user_input_keys()[5], None)
        self.address2 = user_input.get(self.user_input_keys()[6], None)
        self.revisit_time = user_input.get(self.user_input_keys()[7], None)
        self.revisit_date = user_input.get(self.user_input_keys()[8], None)
        self.user_memo = user_input.get(self.user_input_keys()[9], None)
        self._validate()

    def _validate(self):
        if not re.match('^([0]{1}[1]{1}[016789]{1})([0-9]{3,4})([0-9]{4})$', self.phone_number):
            raise ValueError(u'잘못된 전화번호입니다.')

        if len(self.user_memo) > 200:
            raise ValueError(u'메모가 너무 깁니다.')

        if len(self.address1) > 200:
            raise ValueError(u'address1이 너무 깁니다.')

        if len(self.address2) > 200:
            raise ValueError(u'address2가 너무 깁니다.')

        if current_user.phone:
            if current_user.phone != self.phone_number:
                raise ValueError(u'연락처 정보가 다릅니다.')

        start_time = escape(session.get('start_time'))
        converted_start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        day_standard_time1 = converted_start_time.replace(hour=17, minute=0)  # 저녁 5시 기준
        day_standard_time2 = converted_start_time.replace(hour=23, minute=59, second=59)

        if converted_start_time > day_standard_time1 and converted_start_time <= day_standard_time2:
            converted_visit_date = datetime.datetime.strptime(self.visit_date, "%Y-%m-%d")
            converted_revisit_date = datetime.datetime.strptime(self.revisit_date, "%Y-%m-%d")
            today = datetime.datetime.now()
            tommorrow = today + datetime.timedelta(days=1)

            if converted_visit_date <= tommorrow or converted_revisit_date <= tommorrow:
                raise ValueError(u'오후 5시가 넘어 내일을 방문예정일로 설정할 수 없습니다.')

    def serialize(self):
        return {
            'optionsRevisit': self.revisit_option,
            'inputPhoneNumber': self.phone_number,
            'inputVisitDate': self.visit_date,
            'inputPostCode': self.post_code,
            'inputVisitTime': self.visit_time,
            'inputAddress1': self.address1,
            'inputAddress2': self.address2,
            'inputRevisitDate': self.revisit_date,
            'inputRevisitTime': self.revisit_time,
            'textareaMemo': self.user_memo,
        }


class ReservationSerializableFactory(UserInputSerializableFactory):

    reservation_factory = [ReservationEstimate, ReservationOrder]

    @classmethod
    def serializable(cls, user_input_type):
        serializable_cls = cls.find_reservation_serializable_by_type(user_input_type)
        return serializable_cls()

    @classmethod
    def find_reservation_serializable_by_type(cls, user_input_type):
        for reservation_serializable in cls.reservation_factory:
            if reservation_serializable.__user_input_type__ == user_input_type:
                return reservation_serializable
        raise NotImplementedError()

