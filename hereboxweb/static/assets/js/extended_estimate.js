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

    var estimateInfo = Cookies.get('estimate');
    if (!estimateInfo) {
        allowUnload = true;
        purchaseCookieClear();
        location.href = '/my_stuff';
    }

    estimateInfo = $.parseJSON(decode_cookie(estimateInfo));

    var changeTotalPrice = function(direction, count) {
        var totalPrice = 0;

        var stuffs = $(".item");
        stuffs.each(function () {
            var goodsId = $(this).find(".item-box > p > span#goods_id").text();
            var currentPrice = 0;
            var currentPeriod = Number($(this).find('#period').text());
            if (goodsId.startsWith("A")) {
                currentPrice = (7500 * currentPeriod);
            } else {
                currentPrice = (9900 * currentPeriod);
            }
            totalPrice += currentPrice;
            $('#totalExtendPrice').text(numeral(totalPrice).format('0,0'));
            estimateInfo[goodsId] = currentPeriod;
        });

        if (totalPrice < 0) {
            totalPrice = 0;
        }
        $('#totalPrice').text(numeral(totalPrice).format('0,0'));
        return totalPrice;
    };

    var stuffs = $(".item");
    stuffs.each(function () {
        new HereboxCounter($(this).find('.subtract'), $(this).find('.add'), $(this).find('.number'),
            changeTotalPrice
        );

        var goodsId = $(this).find(".item-box > p > span#goods_id").text();

        if (estimateInfo && estimateInfo[goodsId]) {
            var oldGoodsCount = estimateInfo[goodsId];
            $(this).find('.number').text(oldGoodsCount);
        }
    });

    var startTime = moment().format('YYYY-MM-DD HH:mm:ss');
    changeTotalPrice();

    $('#btnCheckPromotion').click(function() {
        alert("해당되는 프로모션이 없습니다.");
    });

    $('#btnNextStep').click(function() {
        allowUnload = true;

        $.ajax({
             type: "POST",
             url: "/extended/review",
             data: {estimate: JSON.stringify(estimateInfo), totalPrice: changeTotalPrice(),
                 startTime: startTime
             },
             success: function () {
                location.href = '/extended/review'
             },
             error: function(request, status, error) {
                var parsedBody = $.parseJSON(request.responseText);
                alert(parsedBody['message']);
             }
        });
    });
});