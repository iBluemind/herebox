# -*- coding: utf-8 -*-


from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, Optional

from hereboxweb.utils import RequiredIf


class LoginForm(Form):
    email = StringField(u'이메일 주소', validators=[DataRequired(message=u'이메일 주소를 입력해주세요')])
    password = PasswordField(u'비밀번호', validators=[DataRequired(message=u'비밀번호를 입력해주세요')])


class SignupForm(Form):
    email = StringField(u'이메일 주소', validators=[DataRequired(message=u'이메일 주소는 반드시 입력해야 합니다'), Email(message=
                                                                                            u'올바른 이메일 주소를 입력해주세요')])
    name = StringField(u'이름', validators=[DataRequired(message=u'이름은 반드시 입력해야 합니다'), Length(
                                min=2, max=6, message=u'이름은 최소 2자, 최대 6자 입력 가능합니다'
                        )])
    password = PasswordField(u'비밀번호', validators=[DataRequired(message=u'비밀번호는 반드시 입력해야 합니다'), Length(
                                min=6, max=16, message=u'비밀번호는 최소 6자, 최대 16자 입력 가능합니다'
                            )])
    password_check = PasswordField(u'비밀번호 확인', validators=[DataRequired(message=u'비밀번호 확인도 반드시 입력해야 합니다'),
                                                                EqualTo('password',
                                                                        message=u'비밀번호를 확인해주세요')])


class ChangeForm(Form):
    email = StringField(u'이메일 주소', validators=[Email(message=u'올바른 이메일 주소를 입력해주세요'), Optional()])
    password = PasswordField(u'비밀번호', validators=[Length(
                    min=6, max=16, message=u'비밀번호는 최소 6자, 최대 16자 입력 가능합니다'
                ), Optional()])
    password_check = PasswordField(u'비밀번호 확인', validators=[RequiredIf('password'), EqualTo('password',
                                                               message=u'비밀번호를 확인해주세요')])
    address1 = StringField(u'주소', validators=[Length(
                                                     max=60, message=u'주소는 최대 60자 입력 가능합니다'
                                                ), Optional()])
    address2 = StringField(u'상세주소', validators=[Length(
                                                     max=60, message=u'상세주소는 최대 60자 입력 가능합니다'
                                                ), Optional()])
    phone = StringField(u'핸드폰 번호', validators=[Optional(),
                                               Regexp(message=u'올바른 휴대폰 번호를 입력해주세요',
                                          regex='^([0]{1}[1]{1}[016789]{1})([0-9]{3,4})([0-9]{4})$')])