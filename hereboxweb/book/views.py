# -*- coding: utf-8 -*-

from flask import request, render_template
from flask.ext.login import login_required

from hereboxweb import database, response_template
from hereboxweb.book.models import *
from hereboxweb.book import book


@book.route('/my_stuff', methods=['GET'])
@login_required
def my_stuff():
    return render_template('my_stuff.html', active_my_index='my_stuff')