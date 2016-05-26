$(document).ready(function() {
    $('#btnSubmit').click(function() {
        $.ajax({
             type: "POST",
             url: "/findpw",
             data: {email: $("#email").val()
             },
             success: function () {
                alert("잠시 후 이메일의 받은 편지함을 확인해주세요.");
             },
             error: function(request, status, error) {
                var parsedBody = $.parseJSON(request.responseText);
                alert(parsedBody['message']);
             }
        });
    });
});
