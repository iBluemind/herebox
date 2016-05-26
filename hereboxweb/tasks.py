# -*- coding: utf-8 -*-


from flask.ext.mail import Message
import coolsms
from celery import Celery
from config import RABBIT_MQ_USER, RABBIT_MQ_HOST, RABBIT_MQ_PASSWORD, RABBIT_MQ_PORT, RABBIT_MQ_VHOST, COOLSMS_API_KEY, \
    COOLSMS_API_KEY_SECRET
from hereboxweb.auth.models import User


tasks = Celery(broker='amqp://%s:%s@%s:%s/%s' % (RABBIT_MQ_USER, RABBIT_MQ_PASSWORD, RABBIT_MQ_HOST,
                                                 RABBIT_MQ_PORT, RABBIT_MQ_VHOST))


@tasks.task
def send_sms_to_user(uid, message):
    user = User.query.get(uid)
    if user:
        phone = user.phone
        cool = coolsms.rest(COOLSMS_API_KEY, COOLSMS_API_KEY_SECRET)
        status = cool.send(phone, message, '16002964')


@tasks.task
def send_sms(phone, message):
    cool = coolsms.rest(COOLSMS_API_KEY, COOLSMS_API_KEY_SECRET)
    status = cool.send(phone, message, '16002964')


@tasks.task
def send_mms(phone, message, subject):
    cool = coolsms.rest(COOLSMS_API_KEY, COOLSMS_API_KEY_SECRET)
    status = cool.send(phone, message, '16002964', mtype='lms', subject=subject)


@tasks.task
def send_mail(subject, message, to):
    mail_msg = Message(body=message,
                       subject=subject,
                       sender="contact@herebox.kr",
                       recipients=[to])

    from hereboxweb import mail, app
    with app.app_context():
        mail.send(mail_msg)