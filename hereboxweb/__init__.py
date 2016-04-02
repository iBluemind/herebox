# -*- coding: utf-8 -*-
import logging

from flask import Flask
from hereboxweb.connector import DBConnector, DBConnectHelper, DBType, DBConnectorType
    # RedisConnectHelper, RedisType

app = Flask(__name__)

# SQLAlchemy URI 설정
from config import SQLALCHEMY_ECHO, SQLALCHEMY_POOL_RECYCLE, \
    SQLALCHEMY_POOL_SIZE, response_template
    # REDIS_PASSWORD, REDIS_PORT,REDIS_HOST,

app.config['SQLALCHEMY_ECHO'] = SQLALCHEMY_ECHO
app.config['SQLALCHEMY_POOL_RECYCLE'] = SQLALCHEMY_POOL_RECYCLE
app.config['SQLALCHEMY_POOL_SIZE'] = SQLALCHEMY_POOL_SIZE

db_helper = DBConnectHelper(app)
database = db_helper.get_db(DBConnectorType.USE_SQLALCHEMY, DBType.MAIN_DB)

# Redis
# redis_sessions = RedisConnectHelper(RedisType.SESSION_REDIS)

# SECRET KEY 설정
# from config import GEARCOACH_SECRET_KEY
# app.secret_key = GEARCOACH_SECRET_KEY

# Status 400 응답
@app.errorhandler(400)
def bad_request(message=u'잘못된 형식으로 요청했습니다.', error=None):
    if type(message) is not unicode:
        message = str(message)
    return response_template(message, 400)

# Status 401 응답
@app.errorhandler(401)
def unauthorized(message=u'로그인이 필요합니다.', error=None):
    if type(message) is not unicode:
        message = str(message)
    return response_template(message, 401)

# Status 403 응답
@app.errorhandler(403)
def forbidden(message=u'권한이 없습니다.', error=None):
    if type(message) is not unicode:
        message = str(message)
    return response_template(message, 403)

# Status 404 응답
@app.errorhandler(404)
def not_found(message=u'잘못된 요청입니다. 요청 API를 확인해주세요.', error=None):
    if type(message) is not unicode:
        message = str(message)
    return response_template(message, 404)

# Status 500 응답
@app.errorhandler(500)
def internal_error(message=u'점검 중이거나 내부 문제가 발생했습니다. 나중에 다시 시도해주세요.', error=None):
    if type(message) is not unicode:
        message = str(message)
    return response_template(message, 500)


# API 컨트롤러 모듈
from hereboxweb.landing.views import landing
app.register_blueprint(landing)

# database.create_all()