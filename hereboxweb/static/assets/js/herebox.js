
function purchaseCookieClear() {
	Cookies.remove('estimate', { path: '/reservation/' });
    Cookies.remove('order', { path: '/reservation/' });
    Cookies.remove('totalPrice', { path: '/reservation/' });
    Cookies.remove('estimate', { path: '/extended/' });
    Cookies.remove('order', { path: '/extended/' });
    Cookies.remove('estimate', { path: '/delivery/' });
    Cookies.remove('order', { path: '/delivery/' });
    Cookies.remove('totalPrice', { path: '/delivery/' });
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
