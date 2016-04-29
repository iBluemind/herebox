$(document).ready(function() {
    var orderInfo = Cookies.get('order');
    if (!orderInfo) {
        purchaseCookieClear();
        location.href = '/';
    }
    orderInfo = $.parseJSON(decode_cookie(orderInfo));
    if (!orderInfo['total_price']) {
        purchaseCookieClear();
        location.href = '/';
    }
});