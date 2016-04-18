# -*- coding: utf-8 -*-

from flask import request, render_template
from flask.ext.login import login_required
from hereboxweb import database, response_template
from hereboxweb.payment import payment
from hereboxweb.payment.models import *


@payment.route('/reservation/payment', methods=['GET'])
@login_required
def reservation_payment():
    return render_template('payment.html', active_my_index='my_schedule')

