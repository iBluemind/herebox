# -*- coding: utf-8 -*-

import coolsms
from celery import Celery
from gcm import GCM
from config import RABBIT_MQ_USER, RABBIT_MQ_HOST, RABBIT_MQ_PASSWORD, RABBIT_MQ_PORT, RABBIT_MQ_VHOST, COOLSMS_API_KEY, \
    COOLSMS_API_KEY_SECRET
from hereboxweb import database
from hereboxweb.auth.models import User
from hereboxweb.schedule.models import Reservation, ReservationStatus


tasks = Celery(broker='amqp://%s:%s@%s:%s/%s' % (RABBIT_MQ_USER, RABBIT_MQ_PASSWORD, RABBIT_MQ_HOST,
                                                 RABBIT_MQ_PORT, RABBIT_MQ_VHOST))


@tasks.task
def send_sms_to_user(uid, message):
    user = User.query.get(uid)
    if user:
        phone = user.phone
        cool = coolsms.rest(COOLSMS_API_KEY, COOLSMS_API_KEY_SECRET)
        status = cool.send(phone, message, '01064849686')


@tasks.task
def send_sms(phone, message):
    cool = coolsms.rest(COOLSMS_API_KEY, COOLSMS_API_KEY_SECRET)
    status = cool.send(phone, message, '01064849686')