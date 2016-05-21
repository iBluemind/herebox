# -*- coding: utf-8 -*-


import json
from abc import ABCMeta, abstractmethod
from hereboxweb import bad_request


class UserInputSerializable(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def user_input_keys(self):
        pass

    @abstractmethod
    def deserialize(self, user_input):
        pass

    @abstractmethod
    def serialize(self):
        pass


class UserInputSerializableFactory(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def serializable(self, user_input_type):
        pass


class SerializableStoreManager(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, serializable, cookies):
        pass

    @abstractmethod
    def save(self, serializable, form, **kwargs):
        pass


class CookieSerializableStoreManager(SerializableStoreManager):

    @classmethod
    def get(cls, serializable, cookies):
        user_data = cookies.get(serializable.__user_input_type__)
        if user_data:
            return serializable.serialize(user_data)

    @classmethod
    def save(cls, serializable, form, **kwargs):
        kwargs['response'].set_cookie(serializable.__user_input_type__,
                            json.dumps(serializable.serialize(form)), path=kwargs['api_endpoint'])
        return kwargs['response']


class PurchaseStepManager(object):

    def __init__(self, serializable, store_manager):
        self.serializable = serializable
        self.user_input_type = serializable.__user_input_type__
        self.store_manager = store_manager

    def serialize(self):
        estimate_keys = self.serializable.user_input_keys()
        user_estimate = PurchaseStepManager.extract_user_input(self.user_input_type, estimate_keys)

        try:
            PurchaseStepManager.validate_user_input(user_estimate, estimate_keys)
            self.serializable.deserialize(user_estimate)
        except KeyError as error:
            return bad_request(error.message)
        except ValueError:
            return bad_request()

        return self.serializable.serialize()

    def get(self, cookies):
        return self.store_manager.get(self.serializable, cookies)

    def save(self, form, response, api_endpoint):
        return self.store_manager.save(self.serializable, form, response=response, api_endpoint=api_endpoint)

    @staticmethod
    def validate_user_input(user_input, keys):
        for key in keys:
            if not key in user_input.keys():
                raise KeyError('%s을(를) 찾을 수 없습니다.' % key)

    @staticmethod
    def extract_user_input(user_input, keys):
        extracted = {}
        for key in keys:
            extracted[key] = user_input.get(key, None)
        return extracted