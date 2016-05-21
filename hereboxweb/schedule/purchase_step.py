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
    def get(cls, serializable, cookies, serialize=None):
        user_data = cookies.get(serializable.__user_input_type__)
        if user_data:
            if serialize:
                try:
                    serialize(user_data)
                except:
                    raise
            else:
                serializable.serialize(user_data)
            return serializable

    @classmethod
    def save(cls, serializable, form, **kwargs):
        serialize = kwargs.get('serialize')
        serialized = None
        if serialize:
            try:
                serialized = serialize(form)
            except KeyError as error:
                return bad_request(error.message)
            except ValueError:
                return bad_request()
        else:
            serialized = serializable.serialize(form)
        kwargs['response'].set_cookie(serializable.__user_input_type__,
                            json.dumps(serialized), path=kwargs['api_endpoint'])
        return kwargs['response']


class PurchaseStepManager(object):

    def __init__(self, serializable, store_manager):
        self.serializable = serializable
        self.user_input_type = serializable.__user_input_type__
        self.store_manager = store_manager

    def serialize(self, user_input):
        user_input_keys = self.serializable.user_input_keys()
        if type(user_input) is not dict:
            user_input = json.loads(user_input)
        user_data = PurchaseStepManager.extract_user_input(user_input, user_input_keys)

        try:
            PurchaseStepManager.validate_user_input(user_data, user_input_keys)
            self.serializable.deserialize(user_data)
        except:
            raise

        return self.serializable.serialize()

    def get(self, cookies):
        return self.store_manager.get(self.serializable, cookies, serialize=self.serialize)

    def save(self, form, response, api_endpoint):
        dict_form = dict(form)
        for key in dict_form:
            dict_form[key] = dict_form[key][0]
        return self.store_manager.save(self.serializable, dict_form,
                                       response=response, api_endpoint=api_endpoint,
                                       serialize=self.serialize)

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