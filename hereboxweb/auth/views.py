# -*- coding: utf-8 -*-


import base64
import re
import urllib
import urllib2
import urlparse

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from flask import request, render_template, make_response
from flask.ext.login import login_required, login_user, logout_user, current_user
from flask.ext.mobility.decorators import mobile_template
from sqlalchemy.exc import IntegrityError
from flask import request, url_for, redirect, flash, session, escape
from hereboxweb import database, response_template, bad_request, unauthorized, login_manager, auth_code_redis, forbidden
from hereboxweb.auth import auth
from hereboxweb.auth.crypto import AESCipher
from hereboxweb.auth.forms import LoginForm, SignupForm, ChangeForm
from hereboxweb.auth.models import User
from config import RSA_PUBLIC_KEY_BASE64
from config import RSA_PRIVATE_KEY_BASE64
from hereboxweb.tasks import send_sms


@auth.route('/login', methods=['GET', 'POST'])
@mobile_template('{mobile/}login.html')
def login(template):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    rsa_public_key = RSA_PUBLIC_KEY_BASE64

    if form.validate_on_submit():
        encoded_email = form.email.data
        encoded_password = form.password.data
        encoded_aes_key = request.form['decryptKey']
        encoded_aes_iv = request.form['iv']

        try:
            encrypted_email = base64.b64decode(encoded_email)
            encrypted_password = base64.b64decode(encoded_password)
            encrypted_aes_key = base64.b64decode(encoded_aes_key)
            aes_iv = base64.b64decode(encoded_aes_iv)

            decoded_private_key = base64.b64decode(RSA_PRIVATE_KEY_BASE64)
            private_key = PKCS1_OAEP.new(RSA.importKey(decoded_private_key))

            decrypted_aes_key = private_key.decrypt(encrypted_aes_key)
            aes_cipher = AESCipher(decrypted_aes_key)

            decrypted_email = aes_cipher.decrypt(encrypted_email, aes_iv)
            decrypted_password = aes_cipher.decrypt(encrypted_password, aes_iv)

            query = database.session.query(User).filter(User.email == decrypted_email)
            user = query.first()

            if user.check_password(decrypted_password):
                flash(u'환영합니다')
                login_user(user)
                return redirect(request.args.get('next') or url_for('index'))
            else:
                raise
        except:
            form.email.errors.append(u'이메일 주소 또는 비밀번호를 다시 확인해주세요.')

    form.email.data = ''
    response = make_response(render_template('login.html', form=form, active_menu='login'))
    if request.MOBILE:
        response = make_response(render_template(template, form=form, active_menu='login'))
    response.set_cookie('jsessionid', rsa_public_key, path='/login')
    return response


@auth.route('/signup', methods=['GET', 'POST'])
@mobile_template('{mobile/}signup.html')
def signup(template):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = SignupForm()
    if form.validate_on_submit():
        name = form.name.data
        password = form.password.data
        email = form.email.data

        new_user = User(name=name, password=password, email=email)

        try:
            database.session.add(new_user)
            database.session.commit()
            return redirect(url_for('index'))
        except IntegrityError, e:
            if '1062' in e.message:
                form.email.data = ''
                form.email.errors.append(u'이미 존재하는 이메일 주소입니다.')
    if request.MOBILE:
        return render_template(template, form=form)
    return render_template('signup.html', form=form)


@auth.route('/fb_login', methods=['POST'])
def fb_login():
    def exchange_access_token(short_access_token):
        args = {}
        args['client_id'] = '1192468164126169'
        args['client_secret'] = 'adc3015c15af6235f1fd3ba3f29ab1a6'
        args['grant_type'] = 'fb_exchange_token'
        args['fb_exchange_token'] = short_access_token

        url = 'https://graph.facebook.com/oauth/access_token'
        encoded_args = urllib.urlencode(args)
        fb_api = '%s?%s' % (url, encoded_args)
        response = urllib2.urlopen(fb_api).read()

        decoded_response = dict(urlparse.parse_qsl(response))
        return decoded_response['access_token']

    user_id = request.form.get('user_id')
    access_token = request.form.get('access_token')
    email = request.form.get('email')
    name = request.form.get('name')

    if not user_id or not access_token:
        return bad_request()

    user = User.query.filter(User.fb_user_id == user_id).first()
    if not user:
        long_lived_access_token = exchange_access_token(access_token)
        if not long_lived_access_token:
            return bad_request(u'잘못된 액세스 토큰입니다')
        new_user = User(name, email,  fb_user_id=user_id, fb_access_token=long_lived_access_token)
        try:
            database.session.add(new_user)
            database.session.commit()
            login_user(new_user)
            return redirect(request.args.get('next') or url_for('index'))
        except IntegrityError, e:
            if '1062' in e.message:
                return response_template(u'이미 가입된 회원입니다.', 400)
            return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요', status=500)
    login_user(user)
    return redirect(request.args.get('next') or url_for('index'))


@auth.route('/findpw', methods=['GET'])
def find_pw():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('findpw.html')


# 로그아웃
@auth.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@auth.route('/my_info', methods=['GET', 'POST'])
@mobile_template('{mobile/}my_info.html')
@login_required
def my_info(template):
    form = ChangeForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        address1 = form.address1.data
        address2 = form.address2.data
        phone = form.phone.data

        user = User.query.get(current_user.uid)
        if email and not current_user.email:
            user.email = email

        if current_user.phone != phone if phone else False:
            if not session.pop('phone_authentication', False):
                form.phone.errors.append(u'휴대폰 번호 인증을 먼저 받아주세요')
                return render_template('my_info.html', active_my_index='my_info', form=form)
            else:
                user.phone = phone

        user.address1 = address1
        user.address2 = address2

        if password:
            encrypted_password = User.encrypt_password(password)
            user.password = encrypted_password

        try:
            database.session.commit()
        except IntegrityError, e:
            form.message = u'문제가 발생했습니다. 잠시후 다시 시도해주세요'
            if '1062' in e.message:
                form.message = u'이미 가입된 적이 있는 이메일 주소입니다. 다른 이메일 주소를 입력해주세요'

    if request.MOBILE:
        return render_template(template, active_my_index='my_info', form=form)
    return render_template('my_info.html', active_my_index='my_info', form=form)


@auth.route('/authentication_code', methods=['POST', 'GET'])
@login_required
def authentication_code():
    if request.method == 'GET':
        user_auth_code = request.args.get('authCode')
        if not re.match('^([0-9]{4})$', user_auth_code):
            return bad_request(u'올바른 인증코드를 입력해주세요.')

        auth_codes = auth_code_redis.get_redis()
        if auth_codes.get(user_auth_code) is None:
            return unauthorized(u'인증에 실패했습니다.')

        auth_codes.delete(user_auth_code)
        session['phone_authentication'] = True
        return response_template(u'인증에 성공했습니다.')

    phone = request.form.get('phone')
    if not re.match('^([0]{1}[1]{1}[016789]{1})([0-9]{3,4})([0-9]{4})$', phone):
        return bad_request(u'잘못된 전화번호입니다.')

    import random
    random_number = str(random.randint(1111, 9999))

    auth_codes = auth_code_redis.get_redis()
    auth_codes.set(random_number, current_user.uid)

    send_sms.apply_async(args=[phone, u'[히어박스] 본인확인 인증번호[%s]를 입력해주세요.' % random_number])

    return response_template(u'인증번호를 발송했습니다.')


@login_manager.unauthorized_handler
def unauthorized_login():
    return redirect(url_for('auth.login'))

