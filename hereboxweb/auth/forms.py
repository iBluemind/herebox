# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(Form):
    email = StringField(u'이메일 주소', validators=[DataRequired(message=u'반드시 입력해야 합니다')])
    password = PasswordField(u'비밀번호', validators=[DataRequired(message=u'반드시 입력해야 합니다')])


class SignupForm(Form):
    email = StringField(u'이메일 주소', validators=[DataRequired(message=u'반드시 입력해야 합니다'), Email(message=
                                                                                            u'올바른 이메일 주소를 입력해주세요')])
    name = StringField(u'이름', validators=[DataRequired(message=u'반드시 입력해야 합니다'), Length(
                                min=2, max=6, message=u'최소 2자, 최대 6자 입력 가능합니다'
                        )])
    password = PasswordField(u'비밀번호', validators=[DataRequired(message=u'반드시 입력해야 합니다'), Length(
                                min=6, max=16, message=u'최소 6자, 최대 16자 입력 가능합니다'
                            )])
    password_check = PasswordField(u'비밀번호 확인', validators=[DataRequired(message=u'반드시 입력해야 합니다'),
                                                                EqualTo('password',
                                                                        message=u'비밀번호를 확인해주세요')])