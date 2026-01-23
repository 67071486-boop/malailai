from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import (
    delete_counterbyid,
    query_counterbyid,
    insert_counter,
    update_counterbyid,
)
from wxcloudrun.model import new_counter
from wxcloudrun.response import (
    make_succ_empty_response,
    make_succ_response,
    make_err_response,
)
import json
from datetime import datetime
from wxcloudrun.dao import query_all_corp_auths, update_corp_auth
from wxcloudrun.services.wecom_client import fetch_auth_info, WeComApiError, get_contact_manager
from wxcloudrun.services import token_service


@app.route("/")
def index():
    """
    :return: 返回index页面
    """
    return render_template("index.html")


@app.route("/api/count", methods=["POST"])
def count():
    """
    :return:计数结果/清除结果
    """
    print("[views] /api/count POST请求进来", flush=True)
    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if "action" not in params:
        return make_err_response("缺少action参数")

    # 按照不同的action的值，进行不同的操作
    action = params["action"]

    # 执行自增操作
    if action == "inc":
        counter = query_counterbyid(1)
        if counter is None:
            counter = new_counter(1, 1)
            insert_counter(counter)
        else:
            counter["count"] += 1
            counter["updated_at"] = datetime.utcnow()
            update_counterbyid(counter)
        return make_succ_response(counter["count"])

    # 执行清0操作
    elif action == "clear":
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response("action参数错误")


@app.route("/api/count", methods=["GET"])
def get_count():
    """
    :return: 计数的值
    """
    counter = query_counterbyid(1)
    return (
        make_succ_response(0)
        if counter is None
        else make_succ_response(counter["count"])
    )


@app.route("/api/update_corp_auths", methods=["POST"])
def update_corp_auths():
    """批量更新 `corp_auth` 集合中的授权信息：

    - 遍历所有 corp_auth 文档，使用 `permanent_code` 调用 `fetch_auth_info` 拉取 v2 授权信息
    - 将 v2 响应（JSON 字符串）写回 `auth_corp_info`，并更新 `updated_at`
    返回：成功/失败统计与错误列表
    """
    results = {"updated": 0, "failed": 0, "errors": []}
    docs = query_all_corp_auths()
    for doc in docs:
        try:
            corp_id = doc.get("corp_id")
            permanent_code = doc.get("permanent_code")
            if not corp_id or not permanent_code:
                results["failed"] += 1
                results["errors"].append({"corp_id": corp_id, "error": "missing corp_id or permanent_code"})
                continue
            v2 = fetch_auth_info(corp_id, permanent_code)
            # 保存为 JSON 字符串（与现有字段格式兼容）
            doc["auth_corp_info"] = json.dumps(v2)
            doc["updated_at"] = datetime.utcnow()
            update_corp_auth(doc)
            results["updated"] += 1
        except WeComApiError as e:
            results["failed"] += 1
            results["errors"].append({"corp_id": doc.get("corp_id"), "error": str(e)})
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"corp_id": doc.get("corp_id"), "error": str(e)})
    return make_succ_response(results)


@app.route("/api/department/simplelist", methods=["POST"])
def department_simplelist():
    """测试接口：调用 ContactManager.simplelist_departments，返回部门 ID 列表。

    请求示例：{"access_token": "...", "id": 1}
    """
    try:
        params = request.get_json() or {}
        access_token = params.get("access_token")
        dept_id = params.get("id")
        corp_id = params.get("corp_id")

        # 如果前端未提供 access_token，则尝试通过 corp_id 或者数据库中第一个 corp_auth 获取 permanent_code 并拉取 access_token
        if not access_token:
            # 优先使用请求中提供的 corp_id
            corp_doc = None
            if corp_id:
                # 从数据库查找匹配 corp_id
                all_docs = query_all_corp_auths()
                for d in all_docs:
                    if d.get("corp_id") == corp_id:
                        corp_doc = d
                        break
            # 若未提供或未找到，则使用第一条记录作为回退
            if corp_doc is None:
                all_docs = query_all_corp_auths()
                if not all_docs:
                    return make_err_response("no corp_auth records available to obtain access_token")
                corp_doc = all_docs[0]

            permanent_code = corp_doc.get("permanent_code")
            corp_id = corp_doc.get("corp_id")
            if not permanent_code or not corp_id:
                return make_err_response("corp_auth record missing corp_id or permanent_code")

            access_token = token_service.get_corp_access_token(corp_id, permanent_code)
            if not access_token:
                return make_err_response("unable to obtain access_token for corp_id=" + str(corp_id))

        cm = get_contact_manager()
        data = cm.simplelist_departments(access_token, id=dept_id)
        return make_succ_response(data)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))
