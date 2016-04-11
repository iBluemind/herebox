# -*- coding: utf-8 -*-

from flask import request, render_template
from hereboxweb import database, response_template


# @landing.route('/available', methods=['GET'])
# def is_available_evaluate():
#     return response_template(u'아직 이용 불가합니다.', status=200)
#
#
# @landing.route('/review', methods=['POST'])
# def register_review():
#     author = request.form['author']
#     lecture = request.form['lecture']
#     lecture_id = request.form['lecture_id']
#     title = request.form['title']
#     content = request.form['content']
#     rating = request.form['rating']
#
#     new_review = Review(author, lecture_id, lecture, title, content, rating)
#
#     try:
#         database.session.add(new_review)
#         database.session.commit()
#
#     except:
#         return response_template(u'문제가 발생했습니다.', 400)
#     return response_template(u'등록되었습니다.', status=200)

