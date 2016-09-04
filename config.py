# -*- coding: utf-8 -*-

# 디버그 여부
DEBUG = True

# 포트번호
PORT = 8801

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
SQLALCHEMY_TRACK_MODIFICATIONS = True

RABBIT_MQ_HOST = ''
RABBIT_MQ_USER = ''
RABBIT_MQ_PASSWORD = ''
RABBIT_MQ_PORT = ''
RABBIT_MQ_VHOST = ''

COOLSMS_API_KEY = ''
COOLSMS_API_KEY_SECRET = ''

REDIS_HOST = ''
REDIS_PASSWORD = ''
REDIS_PORT = 0

RSA_PRIVATE_KEY_BASE64 = ''
RSA_PUBLIC_KEY_BASE64 = ''

MAIN_DB_URI = ''
DEV_DB_URI = ''

SENTRY_DSN = ''
SECRET_KEY = ''
AWS_S3_BUCKET_NAME = ''
AWS_S3_REGION = ''
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
CDN_DOMAIN = ''
FACEBOOK_CLIENT_ID = ''
FACEBOOK_CLIENT_SECRET = ''
