# -*- coding: utf-8 -*-

from flask import request, render_template
from flask.ext.login import login_required

from hereboxweb import database, response_template
from hereboxweb.schedule import schedule
from hereboxweb.schedule.models import *


@schedule.route('/my_schedule', methods=['GET'])
@login_required
def my_schedule():
    return render_template('my_schedule.html', active_my_index='my_schedule')


@schedule.route('/reservation/estimate', methods=['GET'])
@login_required
def estimate():
    return render_template('estimate.html')


@schedule.route('/reservation/order', methods=['GET'])
@login_required
def order():
    return render_template('reservation.html')