# -*- coding: utf-8 -*-


from flask import Flask, render_template
from flask.ext.assets import Environment
from flask.ext.login import LoginManager
from flask.ext.mobility import Mobility
from flask.ext.s3 import FlaskS3
from hereboxweb.connector import DBConnector, DBConnectHelper, DBType, DBConnectorType,\
    RedisConnectHelper, RedisType
from hereboxweb.utils import initialize_db, compress, upload_to_s3, build_compressed_assets

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
mobile = Mobility(app)
assets = Environment(app)
s3 = FlaskS3(app)

app.config['CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = 'hEREboXiSthEBeST'

# SQLAlchemy URI 설정
from config import SQLALCHEMY_ECHO, SQLALCHEMY_POOL_RECYCLE, \
    SQLALCHEMY_POOL_SIZE, response_template, SQLALCHEMY_TRACK_MODIFICATIONS

app.config['SQLALCHEMY_ECHO'] = SQLALCHEMY_ECHO
app.config['SQLALCHEMY_POOL_RECYCLE'] = SQLALCHEMY_POOL_RECYCLE
app.config['SQLALCHEMY_POOL_SIZE'] = SQLALCHEMY_POOL_SIZE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

db_helper = DBConnectHelper(app)
database = db_helper.get_db(DBConnectorType.USE_SQLALCHEMY, DBType.MAIN_DB)

# Redis
auth_code_redis = RedisConnectHelper(RedisType.AUTH_CODE_REDIS)

app.config['FLASKS3_BUCKET_NAME'] = 'hereboxweb'
app.config['FLASKS3_REGION'] = 'ap-northeast-2'
app.config['AWS_ACCESS_KEY_ID'] = 'AKIAJPI7VJWOYVCOG5HA'
app.config['AWS_SECRET_ACCESS_KEY'] = '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'
app.config['FLASKS3_FORCE_MIMETYPE'] = True
app.config['FLASK_ASSETS_USE_S3'] = True


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
    return render_template('404.html')


@app.errorhandler(403)
def forbidden_template(error=None):
    return render_template('403.html')


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


# initialize_db()
compress()
# build_compressed_assets()
# upload_to_s3()
