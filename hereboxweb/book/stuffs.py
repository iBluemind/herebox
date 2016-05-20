# -*- coding: utf-8 -*-


import json
import datetime
from flask import request, make_response
from config import response_template
from hereboxweb.book.models import Goods


def save_stuffs(api_endpoint):
    stuff_ids = request.form.get('stuffIds')
    if not stuff_ids:
        return response_template(u'물품 아이디가 없습니다.', status=400)

    stuff_ids = json.loads(stuff_ids)

    stuffs = Goods.query.filter(
        Goods.goods_id.in_(stuff_ids)
    ).limit(10).all()

    if not stuffs:
        return response_template(u'해당되는 물품이 없습니다.', status=400)

    stuff_info = {}
    for stuff in stuffs:
        stuff_info[str(stuff.goods_id)] = 0

    response = make_response(response_template(u'정상 처리되었습니다.'))
    response.set_cookie('estimate', json.dumps(stuff_info), path=api_endpoint)
    return response


def get_stuffs():
    stuffs = request.cookies.get('estimate')
    if stuffs:
        stuffs = json.loads(stuffs)
        imported_stuffs = Goods.query.filter(
            Goods.goods_id.in_(stuffs.keys())
        ).limit(10).all()

        packed_stuffs = []
        for item in imported_stuffs:
            today = datetime.date.today()
            remaining_day = item.expired_at - today
            item.remaining_day = remaining_day.days
            packed_stuffs.append(item)

        return packed_stuffs