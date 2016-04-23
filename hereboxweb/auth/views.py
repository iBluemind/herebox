# -*- coding: utf-8 -*-


import base64
import re

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from flask import request, render_template
from flask.ext.login import login_required, login_user, logout_user, current_user
from sqlalchemy.exc import IntegrityError
from flask import request, url_for, redirect, flash, session, escape
from hereboxweb import database, response_template, bad_request, unauthorized, login_manager, auth_code_redis
from hereboxweb.auth import auth
from hereboxweb.auth.crypto import AESCipher
from hereboxweb.auth.forms import LoginForm, SignupForm
from hereboxweb.auth.models import User
from config import RSA_PUBLIC_KEY_BASE64
from config import RSA_PRIVATE_KEY_BASE64
from hereboxweb.tasks import send_sms


@auth.route('/login', methods=['GET', 'POST'])
def login():
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
                raise Exception(u'잘못된 로그인 시도입니다')
        except:
            return unauthorized(u'이메일 주소 또는 비밀번호를 다시 확인해주세요.')
    return render_template('login.html', form=form, jsessionid=rsa_public_key)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
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
        except IntegrityError, e:
            if '1062' in e.message:
                return response_template(u'이미 가입된 회원입니다.', 400)
        return redirect(url_for('index'))
    return render_template('signup.html', form=form)


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
@login_required
def my_info():
    return render_template('my_info.html', active_my_index='my_info')


@auth.route('/authentication_code', methods=['POST', 'GET'])
@login_required
def authentication_code():
    if request.method == 'GET':
        user_auth_code = request.args.get('authCode')
        print user_auth_code
        if not re.match('^([0-9]{4})$', user_auth_code):
            return bad_request(u'올바른 인증코드를 입력해주세요.')

        auth_codes = auth_code_redis.get_redis()
        if auth_codes.get(user_auth_code) is None:
            return bad_request(u'인증에 실패했습니다.')

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

