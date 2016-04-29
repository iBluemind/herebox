$(document).ready(function () {
    var isBtnAuthCode = false;

    $("#btnAuthCode").click(function () {
        var newUserPhone = $("#phone").val();
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