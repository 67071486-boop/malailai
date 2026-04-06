import json
import hashlib
import secrets
import time
from datetime import datetime, timezone

from flask import request

from wecom.api import api_bp
from wecom.api.helpers import _parse_int
from wecom.dao import (
    delete_counterbyid,
    insert_counter,
    query_all_corp_auths,
    query_corp_auth,
    query_counterbyid,
    query_group_chat,
    query_group_chat_by_name,
    query_group_chats,
    query_pending_orders_paged,
    update_corp_auth,
    update_counterbyid,
)
from wecom.model import new_counter
from wecom.response import make_err_response, make_succ_empty_response, make_succ_response
from wecom.services.service import token_service
from wecom.services.wecom_client import WeComApiError, fetch_auth_info
from wecom.services.wecom import fetch_agent_list


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


@api_bp.route("/v1/group_chats", methods=["GET", "POST"])
def api_group_chats():
    """前端调用：查询客户群。

    入参（GET: query string / POST: JSON body）：
    - chat_id: 客户群唯一 ID（优先级最高，传入则按 chat_id 查询单条）
    - name: 客户群名称（必填于名称查询）
    - corp_id: 企业 ID（可选；与 name 搭配可精确查询）
    - limit: 列表查询数量，默认 50
    - skip: 列表查询偏移量，默认 0

    返回值格式：
    - 单条查询（chat_id 或 name）：{"code": 0, "data": {...}}，未命中则 data 为 null
    - 列表查询：{"code": 0, "data": [ ... ]}
    """
    params = request.get_json(silent=True) if request.method == "POST" else request.args
    params = params or {}
    chat_id = params.get("chat_id")
    corp_id = params.get("corp_id")
    name = params.get("name")

    if chat_id:
        return make_succ_response(query_group_chat(chat_id))
    if name:
        return make_succ_response(query_group_chat_by_name(corp_id, name))

    limit = _parse_int(params.get("limit"), 50)
    skip = _parse_int(params.get("skip"), 0)
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


@api_bp.route("/v1/corp_auth_info", methods=["POST"])
def api_corp_auth_info():
    """前端调用：按 corp_id 查询授权企业信息。"""
    params = request.get_json(silent=True) or {}
    corp_id = params.get("corp_id")
    if not corp_id:
        return make_err_response("missing corp_id")

    doc = query_corp_auth(corp_id)
    if not doc:
        return make_err_response("corp_auth not found")

    auth_corp_info = doc.get("auth_corp_info")
    if not auth_corp_info:
        return make_err_response("auth_corp_info not found")

    if isinstance(auth_corp_info, str):
        try:
            auth_corp_info = json.loads(auth_corp_info)
        except Exception:
            return make_err_response("auth_corp_info parse error")

    return make_succ_response(auth_corp_info)


@api_bp.route("/v1/agent_ids", methods=["POST"])
def api_agent_ids():
    """前端调用：按 corp_id 获取可访问的应用 agentid 列表。"""
    params = request.get_json(silent=True) or {}
    corp_id = params.get("corp_id")
    if not corp_id:
        return make_err_response("missing corp_id")

    corp_doc = query_corp_auth(corp_id)
    if not corp_doc:
        return make_err_response("corp_auth not found")
    permanent_code = corp_doc.get("permanent_code")
    if not permanent_code:
        return make_err_response("permanent_code missing")

    access_token = token_service.get_corp_access_token(corp_id, permanent_code)
    if not access_token:
        return make_err_response("unable to obtain access_token")

    try:
        data = fetch_agent_list(access_token)
        agent_list = data.get("agentlist") or []
        agent_id = None
        for item in agent_list:
            if item.get("agentid") is not None:
                agent_id = item.get("agentid")
                break
        if agent_id is None:
            return make_err_response("agentid not found")
        return make_succ_response({"agentid": agent_id})
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


def _build_jsapi_signature(ticket: str, nonce_str: str, timestamp: int, url: str) -> str:
    raw = f"jsapi_ticket={ticket}&noncestr={nonce_str}&timestamp={timestamp}&url={url}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


@api_bp.route("/v1/jsapi_signature", methods=["POST"])
def api_jsapi_signature():
    """前端调用：生成 JS-SDK 签名（config/agentConfig）。

    请求示例：
    {
      "corp_id": "xxx",
      "url": "https://example.com/path",
      "mode": "corp" | "agent",
      "agent_id": "1000247",
      "js_api_list": ["selectExternalContact"]
    }
    """
    params = request.get_json(silent=True) or {}
    corp_id = params.get("corp_id")
    url = params.get("url")
    mode = params.get("mode", "corp")
    agent_id = params.get("agent_id")
    js_api_list = params.get("js_api_list") or []

    if not corp_id:
        return make_err_response("missing corp_id")
    if not url:
        return make_err_response("missing url")
    if mode not in {"corp", "agent"}:
        return make_err_response("mode must be corp or agent")
    if mode == "agent" and not agent_id:
        return make_err_response("missing agent_id")

    corp_doc = query_corp_auth(corp_id)
    if not corp_doc:
        return make_err_response("corp_auth not found")
    permanent_code = corp_doc.get("permanent_code")
    if not permanent_code:
        return make_err_response("permanent_code missing")

    access_token = token_service.get_corp_access_token(corp_id, permanent_code)
    if not access_token:
        return make_err_response("unable to obtain access_token")

    ticket_type = "agent" if mode == "agent" else "corp"
    ticket = token_service.get_jsapi_ticket_cached(corp_id, ticket_type=ticket_type, agent_id=agent_id)
    if not ticket:
        token_service.fetch_jsapi_ticket(
            access_token,
            corp_id,
            ticket_type=ticket_type,
            agent_id=agent_id,
        )
        ticket = token_service.get_jsapi_ticket_cached(corp_id, ticket_type=ticket_type, agent_id=agent_id)
    if not ticket:
        return make_err_response("unable to obtain jsapi_ticket")

    timestamp = int(time.time())
    nonce_str = params.get("nonceStr") or params.get("nonce_str") or secrets.token_hex(8)
    signature = _build_jsapi_signature(ticket, nonce_str, timestamp, url)

    resp = {
        "corpId": corp_id,
        "timestamp": timestamp,
        "nonceStr": nonce_str,
        "signature": signature,
        "jsApiList": js_api_list,
        "url": url,
    }
    if mode == "corp":
        resp["appId"] = corp_id
    else:
        resp["agentId"] = agent_id
        resp["corpid"] = corp_id
    return make_succ_response(resp)


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
            doc["auth_corp_info"] = v2.get("auth_corp_info")
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
