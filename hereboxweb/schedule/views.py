# -*- coding: utf-8 -*-

from flask import request, render_template
from hereboxweb import database, response_template
from hereboxweb.schedule import schedule
from hereboxweb.schedule.models import *


@schedule.route('/my_schedule', methods=['GET'])
def my_schedule():
    return render_template('my_schedule.html', active_my_index='my_schedule')