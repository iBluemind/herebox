var allowUnload = false;
$(document).ready(function() {
    allowUnload = false;

    $(window).on('beforeunload', function() {
        if (allowUnload) {
            return ;
        } else {
            return '현재 입력된 항목들이 지워집니다! 정말 연장을 취소하시겠습니까?';
        }
    });
    $(window).on('unload', function() {
        if (!allowUnload) {
            purchaseCookieClear();
        }
    });

    $('#btnPrevStep').click(function() {
        allowUnload = true;
        location.href = "/extended/review";
    });

    $('#btnNextStep').click(function() {
        allowUnload = true;
        $.ajax({
             type: "POST",
             url: "/extended/payment",
             data: {optionsPayType: $(":radio[name='optionsPayType']:checked").val()
             },
             success: function () {
                location.href = '/extended/completion';
             },
             error: function(request, status, error) {
                var parsedBody = $.parseJSON(request.responseText);
                alert(parsedBody['message']);
             }
        });
    });
});

$(window).load(function() {
    var orderInfo = Cookies.get('order');
    if (orderInfo) {
        return ;
    }

    orderInfo = $.parseJSON(decode_cookie(orderInfo));
    if (orderInfo['start_time']) {
        return ;
    }

    purchaseCookieClear();
    allowUnload = true;
    location.href = '/';
});