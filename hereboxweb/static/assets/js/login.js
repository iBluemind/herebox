$(document).ready(function() {
    facebookSDKInit();
    login();
});

function login() {
    var userEmail = '';
    $('#frmLogin').ajaxForm({
        beforeSubmit: function(formData, jqForm, options) {
            var key = forge.random.getBytesSync(16);
            var iv = forge.random.getBytesSync(16);
            var cipher = forge.cipher.createCipher('AES-CBC', key);
            var jsessionid = Cookies.get('jsessionid');

            for (var index in formData) {
                if (formData.hasOwnProperty(index)) {
                    if (formData[index].name === 'email') {
                        userEmail = formData[index].value;
                        if (userEmail != '') {
                            cipher.start({iv: iv});
                            cipher.update(forge.util.createBuffer(userEmail));
                            cipher.finish();
                            var encryptedEmail = cipher.output.toHex();
                            formData[index].value = forge.util.encode64(forge.util.hexToBytes(encryptedEmail));
                        }
                    }

                    if (formData[index].name === 'password') {
                        var password = formData[index].value;
                        if (password != '') {
                            cipher.start({iv: iv});
                            cipher.update(forge.util.createBuffer(password));
                            cipher.finish();
                            var encryptedPassword = cipher.output.toHex();
                            formData[index].value = forge.util.encode64(forge.util.hexToBytes(encryptedPassword));
                        }
                    }

                    if (formData[index].name === 'decryptKey') {
                        var decoded = forge.util.decode64(jsessionid);
                        var obj = forge.asn1.fromDer(decoded);
                        var publicKey = forge.pki.publicKeyFromAsn1(obj);
                        var encrypted = publicKey.encrypt(key, 'RSA-OAEP');
                        formData[index].value = forge.util.encode64(encrypted);
                    }

                    if (formData[index].name === 'iv') {
                        formData[index].value = forge.util.encode64(iv);
                    }
                }
            }
            return true;
        },
        success: function(data, status, xhr) {
            var html = $.parseHTML(data);
            var loginHtml = $(html).find('#login').html();
            Cookies.remove('jesseionid', {path: '/login'});
            if (loginHtml) {
                $('#login').html(loginHtml);
                login();
            } else {
                location.href = '/';
            }
        }
    });
    
    $('#btnFacebookLogin').click(function () {
        FB.getLoginStatus(statusChangeCallback);
    });
}

function testAPI() {
    console.log('Welcome!  Fetching your information.... ');
    FB.api('/me', function(response) {
      console.log('Successful login for: ' + response.name);
      document.getElementById('status').innerHTML =
        'Thanks for logging in, ' + response.name + '!';
    });
}

function statusChangeCallback(response) {
    console.log('statusChangeCallback');
    console.log(response);
    if (response.status === 'connected') {
        testAPI();
    } else {
        FB.login(function (response) {
            console.log(response);
        }, {scope: 'public_profile,email'});
    }
}

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