from flask import Response
from bson import json_util


def make_succ_empty_response():
    data = json_util.dumps({"code": 0, "data": {}})
    return Response(data, mimetype="application/json")


def make_succ_response(data):
    data = json_util.dumps({"code": 0, "data": data})
    return Response(data, mimetype="application/json")


def make_err_response(err_msg):
    data = json_util.dumps({"code": -1, "errorMsg": err_msg})
    return Response(data, mimetype="application/json")
