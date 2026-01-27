import json
from datetime import datetime, timezone

from flask import request

from wxcloudrun.api import api_bp
from wxcloudrun.api.helpers import _parse_int
from wxcloudrun.dao import (
    delete_counterbyid,
    insert_counter,
    query_all_corp_auths,
    query_counterbyid,
    query_group_chat,
    query_group_chat_by_name,
    query_group_chats,
    query_pending_orders_paged,
    update_corp_auth,
    update_counterbyid,
)
from wxcloudrun.model import new_counter
from wxcloudrun.response import make_err_response, make_succ_empty_response, make_succ_response
from wxcloudrun.services import token_service
from wxcloudrun.services.wecom_client import WeComApiError, fetch_auth_info, get_contact_manager


@api_bp.route("/count", methods=["POST"])
def count():
    """
    :return:计数结果/清除结果
    """
    print("[api] /api/count POST请求进来", flush=True)
    params = request.get_json(silent=True) or {}

    if "action" not in params:
        return make_err_response("缺少action参数")

    action = params["action"]

    if action == "inc":
        counter = query_counterbyid(1)
        if counter is None:
            counter = new_counter(1, 1)
            insert_counter(counter)
        else:
            counter["count"] += 1
            counter["updated_at"] = datetime.now(timezone.utc)
            update_counterbyid(counter)
        return make_succ_response(counter["count"])

    if action == "clear":
        delete_counterbyid(1)
        return make_succ_empty_response()

    return make_err_response("action参数错误")


@api_bp.route("/count", methods=["GET"])
def get_count():
    counter = query_counterbyid(1)
    return make_succ_response(0) if counter is None else make_succ_response(counter["count"])


@api_bp.route("/v1/health", methods=["GET"])
def api_health():
    return make_succ_response({"ok": True})


@api_bp.route("/v1/group_chats", methods=["GET"])
def api_group_chats():
    """前端调用：查询客户群。"""
    chat_id = request.args.get("chat_id")
    corp_id = request.args.get("corp_id")
    name = request.args.get("name")

    if chat_id:
        return make_succ_response(query_group_chat(chat_id))
    if corp_id and name:
        return make_succ_response(query_group_chat_by_name(corp_id, name))

    limit = _parse_int(request.args.get("limit"), 50)
    skip = _parse_int(request.args.get("skip"), 0)
    filter_doc = {}
    if corp_id:
        filter_doc["corp_id"] = corp_id
    data = query_group_chats(filter_doc, limit=limit, skip=skip)
    return make_succ_response(data)


@api_bp.route("/v1/pending_orders", methods=["GET"])
def api_pending_orders():
    """前端调用：查询待推送订单记录列表。"""
    status = request.args.get("status", "pending")
    limit = _parse_int(request.args.get("limit"), 50)
    skip = _parse_int(request.args.get("skip"), 0)
    data = query_pending_orders_paged(status=status, limit=limit, skip=skip)
    return make_succ_response(data)


@api_bp.route("/update_corp_auths", methods=["POST"])
def update_corp_auths():
    """批量更新 `corp_auth` 集合中的授权信息。"""
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
            doc["auth_corp_info"] = json.dumps(v2)
            doc["updated_at"] = datetime.now(timezone.utc)
            update_corp_auth(doc)
            results["updated"] += 1
        except WeComApiError as e:
            results["failed"] += 1
            results["errors"].append({"corp_id": doc.get("corp_id"), "error": str(e)})
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"corp_id": doc.get("corp_id"), "error": str(e)})
    return make_succ_response(results)


@api_bp.route("/department/simplelist", methods=["POST"])
def department_simplelist():
    """测试接口：调用 ContactManager.simplelist_departments，返回部门 ID 列表。"""
    try:
        params = request.get_json() or {}
        access_token = params.get("access_token")
        dept_id = params.get("id")
        corp_id = params.get("corp_id")

        if not access_token:
            corp_doc = None
            if corp_id:
                all_docs = query_all_corp_auths()
                for d in all_docs:
                    if d.get("corp_id") == corp_id:
                        corp_doc = d
                        break
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