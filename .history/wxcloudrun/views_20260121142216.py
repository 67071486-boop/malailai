from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.response import (
    make_succ_empty_response,
    make_succ_response,
    make_err_response,
)

# 调试模式下不导入数据库相关模块
if app.config.get("DEBUG", False):
    # 调试模式：使用内存存储
    counter_value = 0
else:
    # 生产模式：使用数据库
    from wxcloudrun.dao import (
        delete_counterbyid,
        query_counterbyid,
        insert_counter,
        update_counterbyid,
    )
    from wxcloudrun.model import Counters


@app.route("/")
def index():
    """
    :return: 返回index页面
    """
    return render_template("index.html")


@app.route("/api/count", methods=["GET"])
def get_count():
    """
    :return: 计数的值
    """
    # 简单测试版本，不依赖数据库
    return make_succ_response(0)


@app.route("/api/count", methods=["POST"])
def count():
    """
    :return:计数结果/清除结果
    """
    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if "action" not in params:
        return make_err_response("缺少action参数")

    # 按照不同的action的值，进行不同的操作
    action = params["action"]

    # 执行自增操作
    if action == "inc":
        # 简单测试版本，返回固定值
        return make_succ_response(1)

    # 执行清0操作
    elif action == "clear":
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response("action参数错误")
