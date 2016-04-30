$(document).ready(function() {
    facebookSDKInit();

    $('#btnFacebookSignup').click(function () {
        FB.getLoginStatus(statusChangeCallback);
    });
});
