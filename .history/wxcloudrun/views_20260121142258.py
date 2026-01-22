from datetime import datetime
from flask import render_template, request
from wxcloudrun import app  # 直接从wxcloudrun导入app
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
    if app.config.get("DEBUG", False):
        # 调试模式：返回内存中的值
        return make_succ_response(counter_value)
    else:
        # 生产模式：使用数据库
        counter = Counters.query.filter(Counters.id == 1).first()
        return (
            make_succ_response(0)
            if counter is None
            else make_succ_response(counter.count)
        )


@app.route("/api/count", methods=["POST"])
def count():
    """
    :return:计数结果/清除结果
    """
    global counter_value

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if "action" not in params:
        return make_err_response("缺少action参数")

    # 按照不同的action的值，进行不同的操作
    action = params["action"]

    if app.config.get("DEBUG", False):
        # 调试模式：使用内存存储
        if action == "inc":
            counter_value += 1
            return make_succ_response(counter_value)
        elif action == "clear":
            counter_value = 0
            return make_succ_empty_response()
        else:
            return make_err_response("action参数错误")
    else:
        # 生产模式：使用数据库
        # 执行自增操作
        if action == "inc":
            counter = query_counterbyid(1)
            if counter is None:
                counter = Counters()
                counter.id = 1
                counter.count = 1
                counter.created_at = datetime.now()
                counter.updated_at = datetime.now()
                insert_counter(counter)
            else:
                counter.id = 1
                counter.count += 1
                counter.updated_at = datetime.now()
                update_counterbyid(counter)
            return make_succ_response(counter.count)

        # 执行清0操作
        elif action == "clear":
            delete_counterbyid(1)
            return make_succ_empty_response()

        # action参数错误
        else:
            return make_err_response("action参数错误")
