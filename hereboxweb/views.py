# -*- coding: utf-8 -*-

from flask import redirect, url_for, render_template
from flask.ext.login import current_user
from hereboxweb import app


@app.route('/', methods=['GET'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('book.my_stuff'))
    return render_template('index.html')


@app.route('/introduce', methods=['GET'])
def introduce():
    return render_template('index.html')


@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html')