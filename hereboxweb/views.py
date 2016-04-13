# -*- coding: utf-8 -*-

from flask import render_template
from flask.ext.login import current_user

from hereboxweb import app


@app.route('/', methods=['GET'])
def index():
    # if current_user.is_authenticated:
    #     return render_template('index_logged_in.html')
    return render_template('index.html')


@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html')