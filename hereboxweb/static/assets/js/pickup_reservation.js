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

    var estimateInfo = Cookies.get('estimate');
    if (!estimateInfo) {
        allowUnload = true;
        purchaseCookieClear();
        location.href = '/my_stuff';
    }

    var dateTimePickerVisitDateOptions = {
        format: 'YYYY-MM-DD',
        dayViewHeaderFormat:'YYYY MMMM',
        minDate: moment().add(1, 'd'),
        maxDate: moment().add(15, 'd'),
        locale: 'ko'
    };
    var dateTimePickerRevisitDateOptions = {
        format: 'YYYY-MM-DD',
        dayViewHeaderFormat:'YYYY MMMM',
        useCurrent: false,
        defaultDate: moment().add(2, 'd'),
        minDate: moment().add(2, 'd'),
        maxDate: moment().add(9, 'd'),
        locale: 'ko'
    };

    var current = moment();
    var todayDateOnly = moment().format("YYYY-MM-DD");
    var borderTime1 = moment(todayDateOnly + " 17:00:00");
    var borderTime2 = moment(todayDateOnly + " 23:59:59");
    if (current > borderTime1 && current <= borderTime2) {
        dateTimePickerVisitDateOptions['minDate'] = moment().add(2, 'd');
        dateTimePickerVisitDateOptions['maxDate'] = moment().add(17, 'd');
        dateTimePickerRevisitDateOptions['minDate'] = moment().add(3, 'd');
        dateTimePickerRevisitDateOptions['maxDate'] = moment().add(11, 'd');
    }

    $('#inputVisitDate').datetimepicker(dateTimePickerVisitDateOptions);
    $('#inputRevisitDate').datetimepicker(dateTimePickerRevisitDateOptions);

    $('#inputVisitDate').on('dp.change', function (e) {
        var visitDate = e.date.toString();
        dateTimePickerRevisitDateOptions['minDate'] = moment(visitDate).add(1, 'd');
        dateTimePickerRevisitDateOptions['maxDate'] = moment(visitDate).add(7, 'd');
        dateTimePickerRevisitDateOptions['defaultDate'] = moment(visitDate).add(1, 'd');
        dateTimePickerRevisitDateOptions['date'] = moment(visitDate).add(1, 'd');
        $('#inputRevisitDate').data('DateTimePicker').options(dateTimePickerRevisitDateOptions);
    });

    $('input[type=radio][name=optionsRevisit]').change(function() {
        if (this.value == "immediate") {
            $('#revisitDatetime').fadeOut();
        } else if (this.value == "later") {
            $('#revisitDatetime').fadeIn();
        }
    });

    if ($('input[type=radio][name=optionsRevisit]:checked').val() == "immediate") {
        $('#revisitDatetime').fadeOut();
    } else {
        $('#revisitDatetime').fadeIn();
    }

    $('#btnNextStep').click(function() {
        if (errorCheck()) {
            return;
        }
        allowUnload = true;
        go('review');
    });

    var orderInfo = Cookies.get('order');
    if (orderInfo)
        orderInfo = $.parseJSON(decode_cookie(orderInfo));

    if (orderInfo && orderInfo['inputPhoneNumber']) {
        $('#inputPhoneNumber').val(orderInfo['inputPhoneNumber']);
    }
    if (orderInfo && orderInfo['inputPostCode']) {
        $('#inputPostCode').val(orderInfo['inputPostCode']);
    }
    if (orderInfo && orderInfo['inputAddress1']) {
        $('#inputAddress1').val("{{ address1 }}");
    }
    if (orderInfo && orderInfo['inputAddress2']) {
        $('#inputAddress2').val("{{ address2 }}");
    }
    if (orderInfo && orderInfo['inputVisitDate']) {
        $('#inputVisitDate').val(orderInfo['inputVisitDate']);
    }
    if (orderInfo && orderInfo['inputVisitTime']) {
        $('#inputVisitTime').val(orderInfo['inputVisitTime']);
    }
    if (orderInfo && orderInfo['optionsRevisit']) {
        var oldOptionsRevisit = orderInfo['optionsRevisit'];
        switch (oldOptionsRevisit) {
             case 'immediate':
                 $(":radio[id='optionsImmediate']").attr("checked", true);
                 $(":radio[id='optionsLater']").attr("checked", false);
                 break;
             case 'later':
                 $(":radio[id='optionsImmediate']").attr("checked", false);
                 $(":radio[id='optionsLater']").attr("checked", true);
                 break;
         }
    }
    if (orderInfo && orderInfo['inputRevisitDate']) {
        $('#inputRevisitDate').val(orderInfo['inputRevisitDate']);
    }
    if (orderInfo && orderInfo['inputRevisitTime']) {
        $('#inputRevisitTime').val(orderInfo['inputRevisitTime']);
    }
    if (orderInfo && orderInfo['textareaMemo']) {
        $('#textareaMemo').val("{{ user_memo }}");
    }
});

$(window).load(function() {
    var estimateInfo = Cookies.get('estimate');
    if (estimateInfo) {
        return ;
    }

    purchaseCookieClear();
    allowUnload = true;
    location.href = '/';
});

function go(dest) {
    var inputPhoneNumber = $('#inputPhoneNumber').val();
    var inputPostCode = $('#inputPostCode').val();
    var inputAddress1 = $('#inputAddress1').val();
    var inputAddress2 = $('#inputAddress2').val();
    var inputVisitDate = $('#inputVisitDate').val();
    var inputVisitTime = $('#inputVisitTime').val();
    var optionsRevisit = $(":radio[name='optionsRevisit']:checked").val();
    var inputRevisitDate = $('#inputRevisitDate').val();
    var inputRevisitTime = $('#inputRevisitTime').val();
    var textareaMemo = $('#textareaMemo').val();
    $.ajax({
         type: "POST",
         url: "/pickup/" + dest,
         data: {inputPhoneNumber: inputPhoneNumber, inputPostCode: inputPostCode,
            inputAddress1: inputAddress1, inputAddress2: inputAddress2, inputVisitDate: inputVisitDate,
             inputVisitTime: inputVisitTime, optionsRevisit: optionsRevisit, inputRevisitDate: inputRevisitDate,
             inputRevisitTime: inputRevisitTime, textareaMemo: textareaMemo
         },
         success: function () {
            location.href = '/pickup/' + dest;
         },
         error: function(request, status, error) {
            var parsedBody = $.parseJSON(request.responseText);
            alert(parsedBody['message']);
         }
    });
}

function errorCheck() {
    var isError = false;
    if ($('#inputPhoneNumber').val().length == 0) {
        $('#inputPhoneNumber').addClass('has-error');
        isError = true;
    }
    if ($('#inputPostCode').val().length == 0) {
        $('#inputPostCode').addClass('has-error');
        isError = true;
    }
    if ($('#inputAddress1').val().length == 0) {
        $('#inputAddress1').addClass('has-error');
        isError = true;
    }
    if ($('#inputAddress2').val().length == 0) {
        $('#inputAddress2').addClass('has-error');
        isError = true;
    }

    if (isError) {
        $("html, body").animate({ scrollTop: 0 }, "slow");
    }

    return isError;
}

function execDaumPostcode() {
    new daum.Postcode({
        oncomplete: function(data) {
            // 팝업에서 검색결과 항목을 클릭했을때 실행할 코드를 작성하는 부분.

            // 도로명 주소의 노출 규칙에 따라 주소를 조합한다.
            // 내려오는 변수가 값이 없는 경우엔 공백('')값을 가지므로, 이를 참고하여 분기 한다.
            var fullRoadAddr = data.roadAddress; // 도로명 주소 변수
            var extraRoadAddr = ''; // 도로명 조합형 주소 변수

            // 법정동명이 있을 경우 추가한다. (법정리는 제외)
            // 법정동의 경우 마지막 문자가 "동/로/가"로 끝난다.
            if(data.bname !== '' && /[동|로|가]$/g.test(data.bname)){
                extraRoadAddr += data.bname;
            }
            // 건물명이 있고, 공동주택일 경우 추가한다.
            if(data.buildingName !== '' && data.apartment === 'Y'){
               extraRoadAddr += (extraRoadAddr !== '' ? ', ' + data.buildingName : data.buildingName);
            }
            // 도로명, 지번 조합형 주소가 있을 경우, 괄호까지 추가한 최종 문자열을 만든다.
            if(extraRoadAddr !== ''){
                extraRoadAddr = ' (' + extraRoadAddr + ')';
            }
            // 도로명, 지번 주소의 유무에 따라 해당 조합형 주소를 추가한다.
            if(fullRoadAddr !== ''){
                fullRoadAddr += extraRoadAddr;
            }

            $('#inputPostCode').val(data.zonecode);
            $('#inputAddress1').val(fullRoadAddr);
            $('#inputAddress1').val(data.jibunAddress);

            // 사용자가 '선택 안함'을 클릭한 경우, 예상 주소라는 표시를 해준다.
            if(data.autoRoadAddress) {
                //예상되는 도로명 주소에 조합형 주소를 추가한다.
                var expRoadAddr = data.autoRoadAddress + extraRoadAddr;
                $('#inputAddress1').val('(예상 도로명 주소 : ' + expRoadAddr + ')');

            } else if(data.autoJibunAddress) {
                var expJibunAddr = data.autoJibunAddress;
                $('#inputAddress1').val('(예상 지번 주소 : ' + expJibunAddr + ')');
            }
        }
    }).open();
}