# -*- coding: utf-8 -*-

from celery import Celery
from gcm import GCM
from config import RABBIT_MQ_USER, RABBIT_MQ_HOST, RABBIT_MQ_PASSWORD, RABBIT_MQ_PORT, RABBIT_MQ_VHOST
from hereboxweb import database
from hereboxweb.schedule.models import Reservation, ReservationStatus


tasks = Celery(broker='amqp://%s:%s@%s:%s/%s' % (RABBIT_MQ_USER, RABBIT_MQ_PASSWORD, RABBIT_MQ_HOST,
                                                 RABBIT_MQ_PORT, RABBIT_MQ_VHOST))


@tasks.task
def expire_draft_reservation(id, user_id):
    Reservation.query.filter_by(
        id=id,
        status=ReservationStatus.DRAFT,
        user_id=user_id).delete()
    database.session.commit()


@tasks.task
def get_valid_reservation(id, status, uid):
    return Reservation.query.filter_by(id=id,
                                status=status,
                                user_id=uid).first()