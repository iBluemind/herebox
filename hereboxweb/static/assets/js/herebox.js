
function facebookSDKInit() {
    $.getScript('//connect.facebook.net/en_US/sdk.js', function(){
        FB.init({
            appId: '1192468164126169',
            status : true,
            cookie : true,
            version: 'v2.6'
        });
    });
}

function requestUserProfile(accessToken) {
    FB.api('/me', { fields: 'name, email' }, function(response) {
        $.ajax({
             type: "POST",
             url: "/fb_login",
             data: {user_id: response.id, access_token: accessToken,
                 email: response.email, name: response.name
             },
             success: function () {
                location.href = '/';
             },
             error: function(request, status, error) {
                var parsedBody = $.parseJSON(request.responseText);
                alert(parsedBody['message']);
             }
        });
    });
}

function statusChangeCallback(response) {
    if (response.status === 'connected') {
        var accessToken = response.authResponse.accessToken;
        requestUserProfile(accessToken);
    } else {
        FB.login(function (response) {
            var accessToken = response.authResponse.accessToken;
            requestUserProfile(accessToken);
        }, {scope: 'public_profile,email'});
    }
}

function purchaseCookieClear() {
	Cookies.remove('estimate', { path: '/reservation/' });
    Cookies.remove('order', { path: '/reservation/' });
    Cookies.remove('totalPrice', { path: '/reservation/' });
    Cookies.remove('promotion', { path: '/reservation/' });
    Cookies.remove('estimate', { path: '/extended/' });
    Cookies.remove('order', { path: '/extended/' });
    Cookies.remove('estimate', { path: '/delivery/' });
    Cookies.remove('order', { path: '/delivery/' });
    Cookies.remove('totalPrice', { path: '/delivery/' });
    Cookies.remove('estimate', { path: '/pickup/' });
    Cookies.remove('order', { path: '/pickup/' });
    Cookies.remove('totalPrice', { path: '/pickup/' });
}

function decode_cookie(val) {
    if (val.indexOf('\\') === -1) {
        return val;  // not encoded
    }
    val = val.replace(/\\"/gi, '"');
	val = val.replace(/\\(\d{3})/g, function(match, octal) {
        return String.fromCharCode(parseInt(octal, 8));
    });
	return val.replace('\\\\', '\\');
}

$(document).ready(function(){
    $(window).scroll(function(){
        var y = $(window).scrollTop();
        if (y > 0) {
          $("#top-shadow").css({'display':'block', 'z-index': 0});
          $(".navbar-brand").css({'z-index': 100, 'position': 'relative'});
          $(".navbar li").css({'z-index': 100});
        } else {
          $("#top-shadow").css({'display':'none'});
        }
    });
});
