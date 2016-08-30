#-*- coding: utf-8 -*-


from abc import ABCMeta, abstractmethod
from flask.ext.s3 import url_for
from hereboxweb.schedule.price import IRREGULAR_ITEM_PRICE, REGULAR_ITEM_PRICE


class ApplyPromotion(object):
    def storage_price(self, regular_item_count, irregular_item_count, period):
        raise NotImplementedError()

    def binding_products_price(self, binding_product0_count, binding_product1_count, binding_product2_count,
                               binding_product3_count):
        raise NotImplementedError()

    def total_price(self, regular_item_count, irregular_item_count, period, binding_product0_count,
                    binding_product1_count, binding_product2_count,
                    binding_product3_count):
        raise NotImplementedError()


class HellohbApplyPromotion(ApplyPromotion):

    __promotion_id__ = 1
    __url__ = url_for('static', filename='gen/promotion_hellohb.min.js')

    def storage_price(self, regular_item_count, irregular_item_count, period):
        total_storage_price = 0
        discount_count = 10
        discount_count = discount_count - irregular_item_count
        if discount_count >= 0:
            total_storage_price = total_storage_price + \
                                  (IRREGULAR_ITEM_PRICE * irregular_item_count * (period - 1))
        else:
            total_storage_price = total_storage_price + \
                                  (IRREGULAR_ITEM_PRICE * 10 * (period - 1))
            total_storage_price = total_storage_price + \
                                  (IRREGULAR_ITEM_PRICE * (discount_count * -1) * period)

        if discount_count > 0:
            if regular_item_count > 0:
                discount_count = discount_count - regular_item_count
                if discount_count >= 0:
                    total_storage_price = total_storage_price + \
                                          (REGULAR_ITEM_PRICE * regular_item_count * (period - 1))
                else:
                    total_storage_price = total_storage_price + \
                                          (REGULAR_ITEM_PRICE * 10 * (period - 1))
                    total_storage_price = total_storage_price + \
                                          (REGULAR_ITEM_PRICE * (discount_count * -1) * period)
        else:
            total_storage_price = total_storage_price + \
                                  (REGULAR_ITEM_PRICE * regular_item_count * period)
        return total_storage_price


class FivethousandApplyPromotion(ApplyPromotion):

    __promotion_id__ = 2
    __url__ = url_for('static', filename='gen/promotion_fivethousand.min.js')

    def storage_price(self, regular_item_count, irregular_item_count, period):
        total_storage_price = REGULAR_ITEM_PRICE * period * regular_item_count
        total_storage_price = total_storage_price + (IRREGULAR_ITEM_PRICE * period * irregular_item_count)
        total_storage_price -= 5000
        if total_storage_price < 0:
            total_storage_price = 0
        return total_storage_price


class ApplyPromotionManager(object):

    apply_promotions = [HellohbApplyPromotion, FivethousandApplyPromotion]

    @classmethod
    def apply(cls, promotion_obj):
        for apply_promotion in cls.apply_promotions:
            if apply_promotion.__promotion_id__ == promotion_obj.id:
                return apply_promotion()


