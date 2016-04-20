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
SQLALCHEMY_TRACK_MODIFICATIONS = True

RABBIT_MQ_HOST = '52.79.175.144'
RABBIT_MQ_USER = 'herebox'
RABBIT_MQ_PASSWORD = 'akswhddk8'
RABBIT_MQ_PORT = '5672'
RABBIT_MQ_VHOST = 'hereboxweb'

# REDIS_HOST = 'manjong.org'
# REDIS_PASSWORD = 'manjongredis'
# REDIS_PORT = 6379
# REDIS_DB = 9
#
# GCM_API_KEY = ''

RSA_PRIVATE_KEY_BASE64 = 'MIICXgIBAAKBgQC4KL/ar+LcRLHT7uJjBzzL8GIDWxEJ4d+pLSRlMM7lX5T41KFj2krgG0UCG4KoMs+QPN5xumMnosP42VIFNeWnpp+ayakj780pX4kYi4/+y9z9hBtG6+pQAkQgwhlAu0OiLOCJMoDGbnshUW7tbGk+HaIfU27itzie8aRxLiriVwIDAQABAoGBAJhn+Obl2uyJ2VVYhHiJ+9GXXbYDPqWcDbp3hoBMFV2UbbhEWFBHzuGLD+A/njDO5CItjbY3F2os9NxUFeIECcr6eBGS0g4b5xzN39FeyQm75sC1wgPxkVTUq245LhFUx0CcDRn1CevxLK8CaZ4LWEgsksA/18YrVPEVG+GzjOWxAkEAuagn9oXQhTvfRd+Wsb+hTNmArogZtmIi8ZA8XavP4aOwWktlcKNqYu6A302K85bgKdf4ogsQnQmDfFgd5ZBVHwJBAP3vUz5cHhW8+rlAsEAkY37eplDwU+RFS86IDGChmD1Ld++aR51Z5I1xA4OTz2CVN3TauCIK60JvlLJPMizhU8kCQDPaQ08XEKYlkrZxPCVo4CQWm1ojqQrHXfsZzcJbujPLA/Y0GKDdA1meQ2AayDRAb1tAdrDLZlh1z8Nq2O7E4QECQQDJ8MdMcklilDT3meAQQl/1hu7Qsy6j/A+7ISpmtluxcxDgNNr64YAGk3dt7eAfOMsvXLjOKczJup6P5rdKRa8xAkEAsNx0OORzciCEsLstQUrUhdkNVJPEyLVI/npmJP3XD8rzfNYytdW4ALQXbq5tUNa7H1rLvRAC/xkGv0xdkAFCtw=='
RSA_PUBLIC_KEY_BASE64 = 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC4KL/ar+LcRLHT7uJjBzzL8GIDWxEJ4d+pLSRlMM7lX5T41KFj2krgG0UCG4KoMs+QPN5xumMnosP42VIFNeWnpp+ayakj780pX4kYi4/+y9z9hBtG6+pQAkQgwhlAu0OiLOCJMoDGbnshUW7tbGk+HaIfU27itzie8aRxLiriVwIDAQAB'

