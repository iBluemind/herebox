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

    var dateTimePickerOptions = {
        format: 'YYYY-MM-DD',
        dayViewHeaderFormat:'YYYY MMMM',
        minDate: moment().add(1, 'd'),
        maxDate: moment().add(15, 'd'),
        locale: 'ko'
    };

    var current = moment();
    var todayDateOnly = moment().format("YYYY-MM-DD");
    var borderTime1 = moment(todayDateOnly + " 17:00:00");
    var borderTime2 = moment(todayDateOnly + " 23:59:59");
    if (current > borderTime1 && current <= borderTime2) {
        dateTimePickerOptions['minDate'] = moment().add(2, 'd');
        dateTimePickerOptions['maxDate'] = moment().add(17, 'd');
    }

    $('#inputDeliveryDate').datetimepicker(dateTimePickerOptions);

    var estimateInfo = Cookies.get('estimate');
    if (!estimateInfo) {
        allowUnload = true;
        purchaseCookieClear();
        location.href = '/my_stuff';
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
    if (orderInfo && orderInfo['inputDeliveryDate']) {
        $('#inputDeliveryDate').val(orderInfo['inputDeliveryDate']);
    }
    if (orderInfo && orderInfo['inputVisitTime']) {
        $('#inputDeliveryTime').val(orderInfo['inputDeliveryTime']);
    }
    if (orderInfo && orderInfo['optionsDelivery']) {
        var oldOptionsRevisit = orderInfo['optionsDelivery'];
        switch (oldOptionsRevisit) {
             case 'restore':
                 $(":radio[id='optionsRestore']").attr("checked", true);
                 $(":radio[id='optionsExpire']").attr("checked", false);
                 break;
             case 'expire':
                 $(":radio[id='optionsRestore']").attr("checked", false);
                 $(":radio[id='optionsExpire']").attr("checked", true);
                 break;
         }
    }
    if (orderInfo && orderInfo['textareaMemo']) {
        $('#textareaMemo').val("{{ user_memo }}");
    }

    $("#btnAuthCode").click(function () {
        var newUserPhone = $("#inputPhoneNumber").val();
        var phoneRegex = /^([0]{1}[1]{1}[016789]{1})([0-9]{3,4})([0-9]{4})$/;
        if (!phoneRegex.test(newUserPhone)) {
            alert("핸드폰 번호를 하이픈(-) 없이 입력해주세요.");
            return ;
        }

        $.ajax({
             type: "POST",
             url: "/authentication_code",
             data: {phone: newUserPhone
             },
             success: function () {
                alert("인증번호를 발송했습니다.");
                isBtnAuthCode = true;
             },
             error: function(request, status, error) {
                var parsedBody = $.parseJSON(request.responseText);
                alert(parsedBody['message']);
             }
        });
    });

    var isBtnAuthCode = false;

    $("#btnAuthCodeCheck").click(function () {
        if (!isBtnAuthCode) {
            alert("인증번호 받기 버튼을 먼저 눌러주세요.");
            return ;
        }

        var userAuthCode = $("#inputCode").val();
        var authCodeRegex = /^([0-9]{4})$/;
        if (!authCodeRegex.test(userAuthCode)) {
            alert("올바른 인증코드를 입력해주세요.");
            return ;
        }

        $.ajax({
             type: "GET",
             url: "/authentication_code",
             data: {authCode: userAuthCode
             },
             success: function () {
                alert("인증에 성공했습니다.");
             },
             error: function(request, status, error) {
                var parsedBody = $.parseJSON(request.responseText);
                alert(parsedBody['message']);
             }
        });
    });
});

function go(dest) {
    var inputPhoneNumber = $('#inputPhoneNumber').val();
    var inputPostCode = $('#inputPostCode').val();
    var inputAddress1 = $('#inputAddress1').val();
    var inputAddress2 = $('#inputAddress2').val();
    var inputDeliveryDate = $('#inputDeliveryDate').val();
    var inputDeliveryTime = $('#inputDeliveryTime').val();
    var optionsDelivery= $(":radio[name='optionsDelivery']:checked").val();
    var textareaMemo = $('#textareaMemo').val();
    $.ajax({
         type: "POST",
         url: "/delivery/" + dest,
         data: {inputPhoneNumber: inputPhoneNumber, inputPostCode: inputPostCode,
            inputAddress1: inputAddress1, inputAddress2: inputAddress2, inputDeliveryDate: inputDeliveryDate,
             inputDeliveryTime: inputDeliveryTime, optionsDelivery: optionsDelivery, textareaMemo: textareaMemo
         },
         success: function () {

            location.href = '/delivery/' + dest;
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