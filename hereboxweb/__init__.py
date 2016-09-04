# -*- coding: utf-8 -*-


from flask import Flask, render_template, request
from flask_assets import Environment
from flask_login import LoginManager
from flask_mail import Mail
from flask_mobility import Mobility
from flask_s3 import FlaskS3
from flask_script import Manager
from hereboxweb.connector import DBConnector, DBConnectHelper, DBType, DBConnectorType,\
    RedisConnectHelper, RedisType
from hereboxweb.utils import compress, RedisSessionInterface
import logging


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.session_interface = RedisSessionInterface()
mobile = Mobility(app)
assets = Environment(app)
s3 = FlaskS3(app)
mail = Mail(app)
manager = Manager(app)


def create_logger():
    logger = logging.getLogger('herebox_web_logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    return logger


logger = create_logger()


# Sentry 설정
from raven.contrib.flask import Sentry
from config import SENTRY_DSN, SECRET_KEY
sentry = Sentry(app, dsn=SENTRY_DSN)

app.config['CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = SECRET_KEY

# SQLAlchemy URI 설정
from config import SQLALCHEMY_ECHO, SQLALCHEMY_POOL_RECYCLE, \
    SQLALCHEMY_POOL_SIZE, response_template, SQLALCHEMY_TRACK_MODIFICATIONS, DEBUG

app.config['SQLALCHEMY_ECHO'] = SQLALCHEMY_ECHO
app.config['SQLALCHEMY_POOL_RECYCLE'] = SQLALCHEMY_POOL_RECYCLE
app.config['SQLALCHEMY_POOL_SIZE'] = SQLALCHEMY_POOL_SIZE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

db_helper = DBConnectHelper(app)
database = db_helper.get_db(DBConnectorType.USE_SQLALCHEMY, DBType.MAIN_DB)

# Dev Database
# database = db_helper.get_db(DBConnectorType.USE_SQLALCHEMY, DBType.DEV_DB)

# Redis
auth_code_redis = RedisConnectHelper(RedisType.AUTH_CODE_REDIS)

from config import AWS_S3_BUCKET_NAME, AWS_S3_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, CDN_DOMAIN
app.config['FLASKS3_BUCKET_NAME'] = AWS_S3_BUCKET_NAME
app.config['FLASKS3_REGION'] = AWS_S3_REGION
app.config['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY_ID
app.config['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_ACCESS_KEY
app.config['FLASKS3_FORCE_MIMETYPE'] = True
app.config['FLASK_ASSETS_USE_S3'] = True
app.config['FLASKS3_GZIP'] = True
app.config['FLASKS3_CDN_DOMAIN'] = CDN_DOMAIN
app.config['FLASKS3_USE_HTTPS'] = False


# Status 400 응답
def bad_request(message=u'잘못된 형식으로 요청했습니다.', error=None):
    if type(message) is not unicode:
        message = str(message)
    return response_template(message, 400)

# Status 401 응답
def unauthorized(message=u'로그인이 필요합니다.', error=None):
    if type(message) is not unicode:
        message = str(message)
    return response_template(message, 401)

# Status 403 응답
def forbidden(message=u'권한이 없습니다.', error=None):
    if type(message) is not unicode:
        message = str(message)
    return response_template(message, 403)

# Status 404 응답
def not_found(message=u'잘못된 요청입니다. 요청 API를 확인해주세요.', error=None):
    if type(message) is not unicode:
        message = str(message)
    return response_template(message, 404)

# Status 500 응답
def internal_error(message=u'점검 중이거나 내부 문제가 발생했습니다. 나중에 다시 시도해주세요.', error=None):
    if type(message) is not unicode:
        message = str(message)
    return response_template(message, 500)


@app.errorhandler(404)
def not_found_template(error=None):
    sentry.captureException()
    if 'mobile' in request.headers.get('User-Agent').lower():
        return render_template('mobile/404.html')
    else:
        return render_template('404.html')


@app.errorhandler(403)
def forbidden_template(error=None):
    if 'mobile' in request.headers.get('User-Agent').lower():
        return render_template('mobile/403.html')
    else:
        return render_template('403.html')


@app.errorhandler(500)
def internal_error_template(error=None):
    sentry.captureException()
    if 'mobile' in request.headers.get('User-Agent').lower():
        return render_template('mobile/500.html')
    else:
        return render_template('500.html')


from hereboxweb import views

# API 컨트롤러 모듈
from hereboxweb.schedule.views import schedule
from hereboxweb.auth.views import auth
from hereboxweb.admin.views import admin
from hereboxweb.book.views import book
from hereboxweb.payment.views import payment

app.register_blueprint(schedule)
app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(payment)
app.register_blueprint(book)

compress()

