$(document).ready(function() {
    var totalPrice = Cookies.get('totalPrice');
    if (!totalPrice) {
        purchaseCookieClear();
        location.href = '/';
    }
    purchaseCookieClear();
});