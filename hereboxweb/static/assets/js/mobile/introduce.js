$(document).ready(function() {

    $("#reviewSlider").slick({
        dots: false,
        arrows: false,
        infinte: true,
        autoplay: true,
        autoplaySpeed: 1500,
        slidesToShow: 1,
        slidesToScroll: 1
    });

    $('#btnAreaAlert').click(function () {
        $.ajax({
             type: "POST",
             url: "/alert_new_area",
             data: {area: $('#area').val(), contact: $('#contact').val()
             },
             success: function () {
                alert("감사합니다!");
                $('#requestArea').modal('hide');
             },
             error: function(request, status, error) {
                var parsedBody = $.parseJSON(request.responseText);
                alert(parsedBody['message']);
             }
        });
    });
});