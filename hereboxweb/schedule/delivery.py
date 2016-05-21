# -*- coding: utf-8 -*-


import re
import datetime
from flask import escape, session
from flask.ext.login import current_user
from hereboxweb.schedule.purchase_step import UserInputSerializable, UserInputSerializableFactory


class DeliveryOption(object):
    RESTORE = 'restore'
    EXPIRE = 'expire'


class DeliveryOrder(UserInputSerializable):

    __user_input_type__ = 'order'

    def user_input_keys(self):
        return ['optionsDelivery', 'inputPhoneNumber', 'inputDeliveryDate',
         'inputPostCode', 'inputDeliveryTime', 'inputAddress1',
         'inputAddress2', 'textareaMemo']

    def deserialize(self, user_input):
        self.delivery_option = int(user_input.get(self.user_input_keys()[0], DeliveryOption.RESTORE))
        self.phone_number = user_input.get(self.user_input_keys()[1], None)
        self.visit_date = user_input.get(self.user_input_keys()[2], None)
        self.post_code = user_input.get(self.user_input_keys()[3], None)
        self.visit_time = int(user_input.get(self.user_input_keys()[4], 0))
        self.address1 = user_input.get(self.user_input_keys()[5], None)
        self.address2 = user_input.get(self.user_input_keys()[6], None)
        self.user_memo = user_input.get(self.user_input_keys()[7], None)
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
            today = datetime.datetime.now()
            tommorrow = today + datetime.timedelta(days=1)

            if converted_visit_date <= tommorrow:
                raise ValueError(u'오후 5시가 넘어 내일을 방문예정일로 설정할 수 없습니다.')

    def serialize(self):
        return {
            'optionsDelivery': self.delivery_option,
            'inputPhoneNumber': self.phone_number,
            'inputVisitDate': self.visit_date,
            'inputPostCode': self.post_code,
            'inputVisitTime': self.visit_time,
            'inputAddress1': self.address1,
            'inputAddress2': self.address2,
            'textareaMemo': self.user_memo,
        }


class DeliverySerializableFactory(UserInputSerializableFactory):

    delivery_factory = [DeliveryOrder]

    @classmethod
    def serializable(cls, user_input_type):
        serializable_cls = cls.find_delivery_serializable_by_type(cls, user_input_type)
        return serializable_cls()

    def find_delivery_serializable_by_type(self, user_input_type):
        for delivery_serializable in self.delivery_factory:
            if delivery_serializable.__user_input_type__ == user_input_type:
                return delivery_serializable
        raise NotImplementedError()


def calculate_total_delivery_price(packed_stuffs):
    return 2000 * len(packed_stuffs)