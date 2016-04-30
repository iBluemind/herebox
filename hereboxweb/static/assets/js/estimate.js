var allowUnload = false;
$(document).ready(function() {
    allowUnload = false;

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

    var estimateInfo = Cookies.get('estimate');
    if (estimateInfo)
        estimateInfo = $.parseJSON(decode_cookie(estimateInfo));

    var regularItem = $('#regularItem');
    var regularItemSubtract = regularItem.find('.subtract');
    var regularItemNumber = regularItem.find('.number');
    if (estimateInfo && estimateInfo['regularItemNumberCount']) {
        var oldRegularItemNumberCount = estimateInfo['regularItemNumberCount'];
        regularItemNumber.text(oldRegularItemNumberCount);
    }

    var regularItemAdd = regularItem.find('.add');
    var irregularItem = $('#irregularItem');
    var irregularItemSubtract = irregularItem.find('.subtract');
    var irregularItemNumber = irregularItem.find('.number');
    if (estimateInfo && estimateInfo['irregularItemNumberCount']) {
        var oldIrregularItemNumberCount = estimateInfo['irregularItemNumberCount'];
        irregularItemNumber.text(oldIrregularItemNumberCount);
    }

    var irregularItemAdd = irregularItem.find('.add');
    var disposable = $('#disposable');
    var disposableSubtract = disposable.find('.subtract');
    var disposableNumber = disposable.find('.number');
    if (estimateInfo && estimateInfo['disposableNumberCount']) {
        var oldDisposableNumberCount = estimateInfo['disposableNumberCount'];
        disposableNumber.text(oldDisposableNumberCount);
    }

    var disposableAdd = disposable.find('.add');
    var bindingProduct0 = $('#bindingProduct0');
    var bindingProduct0Subtract = bindingProduct0.find('.subtract');
    var bindingProduct0Number = bindingProduct0.find('.number');
    if (estimateInfo && estimateInfo['bindingProduct0NumberCount']) {
        var oldBindingProduct0NumberCount = estimateInfo['bindingProduct0NumberCount'];
        bindingProduct0Number.text(oldBindingProduct0NumberCount);
    }

    var bindingProduct0Add = bindingProduct0.find('.add');
    var bindingProduct1 = $('#bindingProduct1');
    var bindingProduct1Subtract = bindingProduct1.find('.subtract');
    var bindingProduct1Number = bindingProduct1.find('.number');
    if (estimateInfo && estimateInfo['bindingProduct1NumberCount']) {
        var oldBindingProduct1NumberCount = estimateInfo['bindingProduct1NumberCount'];
        bindingProduct1Number.text(oldBindingProduct1NumberCount);
    }

    var bindingProduct1Add = bindingProduct1.find('.add');
    var bindingProduct2 = $('#bindingProduct2');
    var bindingProduct2Subtract = bindingProduct2.find('.subtract');
    var bindingProduct2Number = bindingProduct2.find('.number');
    if (estimateInfo && estimateInfo['bindingProduct2NumberCount']) {
        var oldBindingProduct2NumberCount = estimateInfo['bindingProduct2NumberCount'];
        bindingProduct2Number.text(oldBindingProduct2NumberCount);
    }

    var bindingProduct2Add = bindingProduct2.find('.add');
    var bindingProduct3 = $('#bindingProduct3');
    var bindingProduct3Subtract = bindingProduct3.find('.subtract');
    var bindingProduct3Number = bindingProduct3.find('.number');
    if (estimateInfo && estimateInfo['bindingProduct3NumberCount']) {
        var oldBindingProduct3NumberCount = estimateInfo['bindingProduct3NumberCount'];
        bindingProduct3Number.text(oldBindingProduct3NumberCount);
    }

    var bindingProduct3Add = bindingProduct3.find('.add');

    if (estimateInfo && estimateInfo['optionsPeriod']) {
        var oldOptionsPeriod = estimateInfo['optionsPeriod'];
        switch (oldOptionsPeriod) {
            case 'disposable':
                $("input:radio[id='optionsDisposable']").attr("checked", true);
                $("input:radio[id='optionsSubscription']").attr("checked", false);
                break;
            case 'subscription':
                $("input:radio[id='optionsSubscription']").attr("checked", true);
                $("input:radio[id='optionsDisposable']").attr("checked", false);
                break;
        }
    }

    var calculateStoragePrice = function() {
        var totalStoragePrice = 0;
        var regularItemNumberCount = Number(regularItemNumber.text());
        var irregularItemNumberCount = Number(irregularItemNumber.text());
        var disposableNumberCount = Number(disposableNumber.text());

        if ($(":radio[name='optionsPeriod']:checked").val() == 'disposable') {
            totalStoragePrice = totalStoragePrice + (7500 * regularItemNumberCount * disposableNumberCount);
            totalStoragePrice = totalStoragePrice + (9900 * irregularItemNumberCount * disposableNumberCount);
        } else {
            totalStoragePrice = totalStoragePrice + (7500 * regularItemNumberCount);
            totalStoragePrice = totalStoragePrice + (9900 * irregularItemNumberCount);
        }

        $('#totalStoragePrice').text(numeral(totalStoragePrice).format('0,0'));
        return totalStoragePrice;
    };

    var calculateBindingProductPrice = function() {
        var totalBindingProductPrice = 0;
        var bindingProduct0NumberCount = Number(bindingProduct0Number.text());
        var bindingProduct1NumberCount = Number(bindingProduct1Number.text());
        var bindingProduct2NumberCount = Number(bindingProduct2Number.text());
        var bindingProduct3NumberCount = Number(bindingProduct3Number.text());

        totalBindingProductPrice = totalBindingProductPrice + 500 * bindingProduct0NumberCount;
        totalBindingProductPrice = totalBindingProductPrice + 500 * bindingProduct1NumberCount;
        totalBindingProductPrice = totalBindingProductPrice + 1500 * bindingProduct2NumberCount;
        totalBindingProductPrice = totalBindingProductPrice + 1000 * bindingProduct3NumberCount;

        $('#totalBindingProductPrice').text(numeral(totalBindingProductPrice).format('0,0'));
        return totalBindingProductPrice;
    };

    var changeTotalPrice = function(direction, count) {
        if (Cookies.get('promotion') && Cookies.get('promotion') == 'HELLOHB') {
            applyHELLOHBPromotion();
        } else {
            var totalPrice = calculateStoragePrice() + calculateBindingProductPrice();
            if (totalPrice < 0) {
                totalPrice = 0;
            }
            $('#totalPrice').text(numeral(totalPrice).format('0,0'));
        }
    };

    changeTotalPrice();

    var regularItemHbCounter = new HereboxCounter(regularItemSubtract, regularItemAdd, regularItemNumber,
        changeTotalPrice
    );
    var irregularItemHbCounter = new HereboxCounter(irregularItemSubtract, irregularItemAdd, irregularItemNumber,
        changeTotalPrice
    );
    var disposableHbCounter = new HereboxCounter(disposableSubtract, disposableAdd, disposableNumber,
        changeTotalPrice
    );
    var bindingProduct0HbCounter = new HereboxCounter(bindingProduct0Subtract, bindingProduct0Add, bindingProduct0Number,
        changeTotalPrice
    );
    var bindingProduct1HbCounter = new HereboxCounter(bindingProduct1Subtract, bindingProduct1Add, bindingProduct1Number,
        changeTotalPrice
    );
    var bindingProduct2HbCounter = new HereboxCounter(bindingProduct2Subtract, bindingProduct2Add, bindingProduct2Number,
        changeTotalPrice
    );
    var bindingProduct3HbCounter = new HereboxCounter(bindingProduct3Subtract, bindingProduct3Add, bindingProduct3Number,
        changeTotalPrice
    );

    $('input[type=radio][name=optionsPeriod]').change(function() {
        changeTotalPrice();
    });

    $('#btnCheckPromotion').click(function() {
        $.ajax({
            type: "GET",
            url: "/promotion/" + $('#inputPromotion').val(),
            success: function (data, textStatus, xhr) {
                alert("프로모션 코드가 확인되었습니다");
                if ("HELLOHB" === $('#inputPromotion').val()) {
                    applyHELLOHBPromotion();
                }
            },
            error: function(request, status, error) {
                var parsedBody = $.parseJSON(request.responseText);
                alert(parsedBody['message']);
            }
        });
    });

    $('#btnNextStep').click(function() {
        if (calculateStoragePrice() == 0) {
            alert("규격박스 또는 비규격 물품을 1개월 이상 주문해주셔야 합니다!");
            return ;
        }

        allowUnload = true;

        var regularItemNumberCount = regularItemNumber.text();
        var irregularItemNumberCount = irregularItemNumber.text();
        var disposableNumberCount = disposableNumber.text();
        var optionsPeriod = $(":radio[name='optionsPeriod']:checked").val();
        var bindingProduct0NumberCount = bindingProduct0Number.text();
        var bindingProduct1NumberCount = bindingProduct1Number.text();
        var bindingProduct2NumberCount = bindingProduct2Number.text();
        var bindingProduct3NumberCount = bindingProduct3Number.text();
        var totalPrice = calculateStoragePrice() + calculateBindingProductPrice();
        var promotion = $('#inputPromotion').val();

        $.ajax({
             type: "POST",
             url: "/reservation/order",
             data: {regularItemNumberCount: regularItemNumberCount,
                 irregularItemNumberCount: irregularItemNumberCount, disposableNumberCount: disposableNumberCount,
                 optionsPeriod: optionsPeriod, bindingProduct0NumberCount: bindingProduct0NumberCount,
                 bindingProduct1NumberCount: bindingProduct1NumberCount, bindingProduct2NumberCount: bindingProduct2NumberCount,
                 bindingProduct3NumberCount: bindingProduct3NumberCount, totalPrice: totalPrice, inputPromotion: promotion
             },
             success: function () {
                location.href = '/reservation/order';
             },
             error: function(request, status, error) {
                var parsedBody = $.parseJSON(request.responseText);
                alert(parsedBody['message']);
             }
        });
    });

    function applyHELLOHBPromotion() {
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
});