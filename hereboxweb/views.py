# -*- coding: utf-8 -*-

from flask import render_template
from hereboxweb import app


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html')