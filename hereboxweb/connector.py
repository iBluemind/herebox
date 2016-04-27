# -*- coding: utf-8 -*-


from contextlib import contextmanager
import redis
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import event, create_engine
from sqlalchemy.exc import DisconnectionError
from sqlalchemy.orm import sessionmaker
from config import REDIS_HOST, REDIS_PASSWORD, REDIS_DB
from config import REDIS_PORT


class DBConnectorType(object):
    USE_SQLALCHEMY  = 0
    USE_DBCONNECTOR = 1


class DBType(object):
    MAIN_DB = 'main_db'


class DBConnectHelper(object):
    DATABASES = {
        # DBType.MAIN_DB:    'mysql+mysqldb://herebox:herebox@manjong.org:3306/herebox?charset=utf8&use_unicode=0',
        DBType.MAIN_DB: 'mysql+mysqldb://hereboxadmin:akswhddk8@hereboxweb.chptj9arzq1g.ap-northeast-2.rds.amazonaws.com:3306/herebox?charset=utf8&use_unicode=0',
    }

    def __init__(self, app):
        self.app = app

    def get_db(self, connector_type, db_type):
        db = None
        if connector_type == DBConnectorType.USE_SQLALCHEMY:
            self.app.config['SQLALCHEMY_DATABASE_URI'] = self.DATABASES[db_type]
            db = SQLAlchemy(self.app)
        if connector_type == DBConnectorType.USE_DBCONNECTOR:
            db = DBConnector(self.app, self.DATABASES[db_type])

        if db:
            event.listen(db.engine, 'checkout', self._checkout_listener)
        return db

    def _checkout_listener(self, dbapi_con, con_record, con_proxy):
        try:
            try:
                dbapi_con.ping(False)
            except TypeError:
                dbapi_con.ping()
        except dbapi_con.OperationalError as exc:
            if exc.args[0] in (2006, 2013, 2014, 2045, 2055):
                raise DisconnectionError()
            else:
                raise


class DBConnector(object):
    def __init__(self, app, uri):
        self.uri = uri
        self.pool_size = 10
        if app.config['SQLALCHEMY_POOL_SIZE']:
            self.pool_size = app.config['SQLALCHEMY_POOL_SIZE']
        self.pool_recycle = 7200
        if app.config['SQLALCHEMY_POOL_RECYCLE']:
            self.pool_recycle = app.config['SQLALCHEMY_POOL_RECYCLE']

        self.engine = create_engine(uri, pool_size=self.pool_size, pool_recycle=self.pool_recycle)
        self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def session(self):
        session = None
        try:
            Session = self.Session
            session = Session()
            yield session
        except:
            raise
        finally:
            if session:
                session.close()


class RedisType(object):
    AUTH_CODE_REDIS = {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
        'password': REDIS_PASSWORD,
        'db': REDIS_DB
    }


class RedisConnectHelper(object):

    def __init__(self, redis_type):
        if not type(RedisType):
            raise TypeError('redis_type must be RedisType!')
        self.pool = self.get_connection_pool(redis_type['host'],
                                             redis_type['port'],
                                             redis_type['password'],
                                             redis_type['db'])

    def get_connection_pool(self, host, port, password, db):
        return redis.ConnectionPool(host=host, port=port, password=password,
                                    db=db, encoding='utf-8')

    def get_redis(self):
        return redis.StrictRedis(connection_pool=self.pool)
