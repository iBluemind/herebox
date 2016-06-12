$(document).ready(function () {
    $("#btnPickup").click(function () {
        var selectedStuffs = [];
        $('.my-herebox-stuff-checkbox input:checked').each(function() {
            selectedStuffs.push($(this).attr('name'));
        });

        $.ajax({
             type: "POST",
             url: "/pickup/order",
             data: {stuffIds: JSON.stringify(selectedStuffs)
             },
             success: function () {
                location.href = '/pickup/order'
             },
             error: function(request, status, error) {
                var parsedBody = $.parseJSON(request.responseText);
                alert(parsedBody['message']);
             }
        });
    });

    $("#btnDelivery").click(function () {
        var selectedStuffs = [];
        $('.my-herebox-stuff-checkbox input:checked').each(function() {
            selectedStuffs.push($(this).attr('name'));
        });

        $.ajax({
             type: "POST",
             url: "/delivery/order",
             data: {stuffIds: JSON.stringify(selectedStuffs)
             },
             success: function () {
                location.href = '/delivery/order';
             },
             error: function(request, status, error) {
                var parsedBody = $.parseJSON(request.responseText);
                alert(parsedBody['message']);
             }
        });
    });

    $("#btnExtend").click(function () {
        // var selectedStuffs = [];
        // $('.my-herebox-stuff-checkbox input:checked').each(function() {
        //     selectedStuffs.push($(this).attr('name'));
        // });
        //
        // $.ajax({
        //      type: "POST",
        //      url: "/extended/estimate",
        //      data: {stuffIds: JSON.stringify(selectedStuffs)
        //      },
        //      success: function () {
        //         location.href = '/extended/estimate'
        //      },
        //      error: function(request, status, error) {
        //         var parsedBody = $.parseJSON(request.responseText);
        //         alert(parsedBody['message']);
        //      }
        // });
        alert("기간 연장은 고객센터로 신청해주세요.");
    });

    $(".btn-extend-single").each(function() {
        $(this).click(function () {
            var selectedStuffs = [];
            var goodsId = $(this).parent().siblings("p").find("span#goodsId").text();
            selectedStuffs.push(goodsId);

            $.ajax({
                 type: "POST",
                 url: "/extended/estimate",
                 data: {stuffIds: JSON.stringify(selectedStuffs)
                 },
                 success: function () {
                    location.href = '/extended/estimate'
                 },
                 error: function(request, status, error) {
                    var parsedBody = $.parseJSON(request.responseText);
                    alert(parsedBody['message']);
                 }
            });
        });
    });

    $(".btn-delivery-single").each(function() {
        $(this).click(function () {
            var selectedStuffs = [];
            var goodsId = $(this).parent().siblings("p").find("span#goodsId").text();
            selectedStuffs.push(goodsId);

            $.ajax({
                 type: "POST",
                 url: "/delivery/order",
                 data: {stuffIds: JSON.stringify(selectedStuffs)
                 },
                 success: function () {
                    location.href = '/delivery/order'
                 },
                 error: function(request, status, error) {
                    var parsedBody = $.parseJSON(request.responseText);
                    alert(parsedBody['message']);
                 }
            });
        });
    });

    $(".btn-pickup-single").each(function() {
        $(this).click(function () {
            var selectedStuffs = [];
            var goodsId = $(this).parent().siblings("p").find("span#goodsId").text();
            selectedStuffs.push(goodsId);

            $.ajax({
                 type: "POST",
                 url: "/pickup/order",
                 data: {stuffIds: JSON.stringify(selectedStuffs)
                 },
                 success: function () {
                    location.href = '/pickup/order'
                 },
                 error: function(request, status, error) {
                    var parsedBody = $.parseJSON(request.responseText);
                    alert(parsedBody['message']);
                 }
            });
        });
    });

    $('.btn-up').click(function() {
        var myStuffContent = $(this).parent(".my-stuff-title").siblings(".my-stuff-content");
        if (myStuffContent.hasClass("hide")) {
            myStuffContent.removeClass("hide");
            myStuffContent.slideDown();
            $(this).find("img").attr("src", "/static/assets/img/icon-btup.png");
        } else {
            myStuffContent.addClass("hide");
            myStuffContent.slideUp();
            $(this).find("img").attr("src", "/static/assets/img/icon-btdown.png");
        }
    });

});