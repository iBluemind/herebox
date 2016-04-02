# -*- coding: utf-8 -*-

# 디버그 여부
import socket
DEBUG = False if socket.gethostname().startswith('manjong') else True

# 포트번호
PORT = 8801

# SECRET KEY
# GEARCOACH_SECRET_KEY = 'gERcoACHiSwiNthEgIF2015'

# 기본 응답 템플릿
def response_template(message, status=200, data=None):
    content = {'message': message}
    if data:
        content = {'message': message, 'data': data}

    import flask
    return flask.jsonify(content), status

# SQLAlchemy 설정
SQLALCHEMY_ECHO = DEBUG
SQLALCHEMY_POOL_RECYCLE = 7200
SQLALCHEMY_POOL_SIZE = 10

# REDIS_HOST = 'manjong.org'
# REDIS_PASSWORD = 'manjongredis'
# REDIS_PORT = 6379
# REDIS_DB = 9
#
# GCM_API_KEY = ''
