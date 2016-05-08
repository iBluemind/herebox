# -*- coding: utf-8 -*-
import re

from flask import redirect, url_for, render_template, request
from flask.ext.login import current_user
from flask.ext.mobility.decorators import mobile_template

from config import response_template
from hereboxweb import app, database, bad_request
from hereboxweb.models import AlertNewArea


@app.route('/', methods=['GET'])
@mobile_template('{mobile/}index.html')
def index(template):
    if current_user.is_authenticated:
        return redirect(url_for('book.my_stuff'))
    if request.MOBILE:
        return render_template(template)
    return render_template('index.html', active_menu='introduce')


@app.route('/introduce', methods=['GET'])
@mobile_template('{mobile/}index.html')
def introduce(template):
    if request.MOBILE:
        return render_template(template)
    return render_template('index.html', active_menu='introduce')


@app.route('/faq', methods=['GET'])
@mobile_template('{mobile/}faq.html')
def faq(template):
    if request.MOBILE:
        return render_template(template)
    return render_template('faq.html', active_menu='faq')


@app.route('/event', methods=['GET'])
@mobile_template('{mobile/}event.html')
def event(template):
    if request.MOBILE:
        return render_template(template)
    return render_template('event.html', active_menu='event')


@app.route('/privacy', methods=['GET'])
def privacy():
    return render_template('privacy.html')


@app.route('/terms', methods=['GET'])
def terms():
    return render_template('terms.html')


@app.route('/alert_new_area', methods=['POST'])
def alert_new_area():
    area = request.form.get('area')
    contact = request.form.get('contact')

    if not area:
        return bad_request(u'지역을 입력해주세요')

    if not contact:
        return bad_request(u'연락처를 남겨주세요')

    if len(area) < 6 or len(area) > 20:
        return bad_request(u'지역은 최소 6자, 최대 20자 입력가능합니다')

    if (not re.match('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', contact)) and\
                    (not re.match('^([0]{1}[1]{1}[016789]{1})([0-9]{3,4})([0-9]{4})$', contact)):
        return bad_request(u'올바른 이메일 주소 또는 핸드폰 번호를 입력해주세요')

    alert = AlertNewArea(area, contact)

    try:
        database.session.add(alert)
        database.session.commit()
    except:
        return response_template(u'문제가 발생했습니다. 나중에 다시 시도해주세요')
    return response_template(u'감사합니다.')
