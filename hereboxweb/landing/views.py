# -*- coding: utf-8 -*-

from flask import request, render_template
from hereboxweb import database, response_template
from hereboxweb.landing import landing


@landing.route('/', methods=['GET'])
def index():
    return render_template('index.html')