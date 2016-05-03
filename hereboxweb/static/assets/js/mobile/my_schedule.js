$(document).ready(function () {
    $('.btn-up').click(function() {
        var myStuffContent = $(this).parent(".my-schedule-item-title").siblings(".my-schedule-item-content");
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