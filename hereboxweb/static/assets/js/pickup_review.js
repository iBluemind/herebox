var allowUnload = false;
$(document).ready(function() {
    $(window).on('beforeunload', function() {
        if (allowUnload) {
            return ;
        } else {
            return '현재 입력된 항목들이 지워집니다! 정말 예약을 취소하시겠습니까?';
        }
    });
    $(window).on('unload', function() {
        if (!allowUnload) {
            purchaseCookieClear();
        }
    });

    $('#btnPrevStep').click(function() {
        allowUnload = true;
        location.href = '/pickup/order';
    });

    $('#btnNextStep').click(function() {
        if (!$("input:checkbox[id='chkAgree']").is(":checked")) {
            alert('이용약관에 동의해주셔야 합니다.');
            return ;
        }

        allowUnload = true;
        location.href = '/pickup/payment';
    });
});

$(window).load(function() {
    var orderInfo = Cookies.get('order');
    if (orderInfo) {
        orderInfo = JSON.parse(decode_cookie(orderInfo));

        if (orderInfo['inputPostCode']) {
            return ;
        }
    }

    purchaseCookieClear();
    allowUnload = true;
    location.href = '/';
});