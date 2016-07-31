#-*- coding: utf-8 -*-


from hereboxweb.schedule.models import PromotionCode, Promotion
from hereboxweb.schedule.reservation import PeriodOption


REGULAR_ITEM_PRICE = 7500
IRREGULAR_ITEM_PRICE = 9900
BINDING_PRODUCT_0_PRICE = 500
BINDING_PRODUCT_1_PRICE = 500
BINDING_PRODUCT_2_PRICE = 1500
BINDING_PRODUCT_3_PRICE = 1000


def calculate_storage_price(regular_item_count, irregular_item_count, period_option, period, promotion=None):
    if period_option == PeriodOption.SUBSCRIPTION:
        # 매월 자동 결제일 경우!
        total_storage_price = REGULAR_ITEM_PRICE * regular_item_count
        return total_storage_price + (IRREGULAR_ITEM_PRICE * irregular_item_count)
    else:
        if promotion:
            promotion_code = PromotionCode.query.join(Promotion).filter(PromotionCode.code==promotion).first()
            if promotion_code:
                promotion_obj = promotion_code.promotion
                from hereboxweb.schedule.promotion import ApplyPromotionManager
                apply_promotion = ApplyPromotionManager.apply(promotion_obj)
                try:
                    return apply_promotion.storage_price(regular_item_count, irregular_item_count, period)
                except NotImplementedError:
                    pass
        total_storage_price = REGULAR_ITEM_PRICE * period * regular_item_count
        return total_storage_price + (IRREGULAR_ITEM_PRICE * period * irregular_item_count)


def calculate_binding_products_price(binding_product0_count, binding_product1_count, binding_product2_count,
                                        binding_product3_count):
    total_binding_products_price = 0
    total_binding_products_price = total_binding_products_price + BINDING_PRODUCT_0_PRICE * binding_product0_count
    total_binding_products_price = total_binding_products_price + BINDING_PRODUCT_1_PRICE * binding_product1_count
    total_binding_products_price = total_binding_products_price + BINDING_PRODUCT_2_PRICE * binding_product2_count
    total_binding_products_price = total_binding_products_price + BINDING_PRODUCT_3_PRICE * binding_product3_count
    return total_binding_products_price


def calculate_total_price(regular_item_count, irregular_item_count, period, period_option, promotion,
                          binding_product0_count, binding_product1_count, binding_product2_count,
                          binding_product3_count):
    total_storage_price = calculate_storage_price(regular_item_count, irregular_item_count,
                                                  period_option,
                                                  period, promotion)

    total_binding_products_price = calculate_binding_products_price(binding_product0_count,
                                                                        binding_product1_count,
                                                                        binding_product2_count,
                                                                        binding_product3_count)

    return total_storage_price + total_binding_products_price