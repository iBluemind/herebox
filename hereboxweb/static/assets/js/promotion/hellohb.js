function applyPromotion() {
    if ($(":radio[name='optionsPeriod']:checked").val() == 'disposable') {
        var totalStoragePrice = 0;
        var totalPrice = calculateBindingProductPrice();
        var regularItemNumberCount = Number(regularItemNumber.text());
        var irregularItemNumberCount = Number(irregularItemNumber.text());
        var disposableNumberCount = Number(disposableNumber.text());
        var promotionItem = '프로모션 할인: ';
        var discountCount = 10;
        discountCount -= irregularItemNumberCount;
        if (discountCount >= 0) {
            totalStoragePrice = totalStoragePrice + (9900 * irregularItemNumberCount * (disposableNumberCount - 1));
        } else {
            totalStoragePrice = totalStoragePrice + (9900 * 10 * (disposableNumberCount - 1));
            totalStoragePrice = totalStoragePrice + (9900 * (discountCount * -1) * disposableNumberCount);
        }

        if (discountCount > 0) {
            if (regularItemNumberCount > 0) {
                discountCount -= regularItemNumberCount;
                if (discountCount >= 0) {
                    totalStoragePrice = totalStoragePrice + (7500 * regularItemNumberCount * (disposableNumberCount - 1));
                } else {
                    totalStoragePrice = totalStoragePrice + (7500 * 10 * (disposableNumberCount - 1));
                    totalStoragePrice = totalStoragePrice + (7500 * (discountCount * -1) * disposableNumberCount);
                }
            }
        } else {
            totalStoragePrice = totalStoragePrice + (7500 * regularItemNumberCount * disposableNumberCount);
        }

        totalPrice = totalStoragePrice + totalPrice;
        if (totalPrice < 0) {
            totalPrice = 0;
        }

        var oldTotalStoragePrice = calculateStoragePrice();
        var subtractDiscount = oldTotalStoragePrice - totalStoragePrice;

        $('#totalStoragePrice').text(numeral(totalStoragePrice).format('0,0'));
        $('#promotionDiscount').text(promotionItem + "-" + numeral(subtractDiscount).format('0,0'));
        $('#promotionDiscount').css({'visibility': 'visible'});
        $('#totalPrice').text(numeral(totalPrice).format('0,0'));
    }
}