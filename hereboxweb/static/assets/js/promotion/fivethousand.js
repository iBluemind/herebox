function applyPromotion() {
    if ($(":radio[name='optionsPeriod']:checked").val() == 'disposable') {
        var totalPrice = calculateBindingProductPrice();
        var promotionItem = '프로모션 할인: ';
        var oldTotalStoragePrice = calculateStoragePrice();
        var totalStoragePrice = oldTotalStoragePrice - 5000;
        if (totalStoragePrice < 0) {
            totalStoragePrice = 0;
        }
        totalPrice = totalStoragePrice + totalPrice;
        var subtractDiscount = oldTotalStoragePrice - totalStoragePrice;
        if (subtractDiscount < 0) {
            subtractDiscount = 0;
        }

        $('#totalStoragePrice').text(numeral(totalStoragePrice).format('0,0'));
        $('#promotionDiscount').text(promotionItem + "-" + numeral(subtractDiscount).format('0,0'));
        $('#promotionDiscount').css({'visibility': 'visible'});
        $('#totalPrice').text(numeral(totalPrice).format('0,0'));
    }
}