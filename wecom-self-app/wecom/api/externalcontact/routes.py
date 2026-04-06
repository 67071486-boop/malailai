from datetime import datetime, timezone

from flask import request

from wxcloudrun.api import api_bp
from wxcloudrun.api.helpers import _resolve_access_token
from wxcloudrun.dao import query_group_chat, query_group_chat_by_name, upsert_group_chat
from wxcloudrun.response import make_err_response, make_succ_response
from wxcloudrun.services.wecom.externalcontact.contact_way_manager import ContactWayApi


def _parse_int(value, default):
    try:
        return int(value)
    except Exception:
        return default


def _is_truthy(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


contact_way_api = ContactWayApi()


@api_bp.route("/v1/externalcontact/groupchat/get", methods=["POST"])
def api_externalcontact_groupchat_get():
    """外部联系人客户群详情查询。

    请求方式：POST（HTTPS）
    请求地址：https://wecom.suqing.chat/api/v1/externalcontact/groupchat/get
    请求参数示例：
    {
        "chat_id": "wrOgQhDgAAMYQiS5ol9G7gK9JVAAAA",
        "corp_id": "ww1234567890",
        "name": "测试群",
        "qr_code": true
    }

    本接口入参（JSON body）：
    - chat_id: 客户群 ID（优先级最高）
    - corp_id: 企业 ID（可选）
    - name: 客户群名称（可选；可与 corp_id 组合）
    - qr_code: 是否触发二维码相关处理（可选，true/false）
    - booster: 额外业务标识（可选，写入 bound.booster）

    返回值格式：
    - {"code": 0, "data": {...}}，未命中则 data 为 null，命中则返回客户群详情
    """
    params = request.get_json(silent=True) or {}
    chat_id = params.get("chat_id")
    corp_id = params.get("corp_id")
    name = params.get("name")
    qr_code = _is_truthy(params.get("qr_code"))
    booster = params.get("booster")

    if chat_id:
        doc = query_group_chat(chat_id)
    elif corp_id and name:
        doc = query_group_chat_by_name(corp_id, name)
    elif name:
        doc = query_group_chat_by_name(None, name)
    else:
        return make_err_response("missing chat_id or name")

    if qr_code and doc:
        join_way = doc.get("join_way") if isinstance(doc.get("join_way"), dict) else None
        qr_code_value = join_way.get("qr_code") if isinstance(join_way, dict) else None
        if not qr_code_value:
            chat_id_for_qr = doc.get("chat_id") or chat_id
            corp_id_for_token = corp_id or doc.get("corp_id")
            if not chat_id_for_qr:
                return make_err_response("missing chat_id for qr_code")
            access_token = _resolve_access_token({"corp_id": corp_id_for_token})
            if not access_token:
                return make_err_response("missing corp_id or corp_auth not found")
            try:
                payload = {
                    "scene": 2,
                    "remark": chat_id_for_qr,
                    "chat_id_list": [chat_id_for_qr],
                }
                add_resp = contact_way_api.add_join_way(
                    access_token,
                    payload,
                    corp_id=corp_id_for_token,
                )
                join_way = add_resp.get("join_way") if isinstance(add_resp, dict) else None
                qr_code_value = join_way.get("qr_code") if isinstance(join_way, dict) else None
                if join_way:
                    doc["join_way"] = join_way
                if qr_code_value:
                    doc["updated_at"] = datetime.now(timezone.utc)
                    upsert_group_chat(doc)
            except Exception as exc:
                print("[api.externalcontact] add_join_way failed", exc, flush=True)

    if booster is not None and doc:
        bound = doc.get("bound") if isinstance(doc.get("bound"), dict) else {}
        query_records = bound.get("query_records")
        if not isinstance(query_records, list):
            query_records = []
        query_records.append({"booster": booster, "created_at": datetime.now(timezone.utc)})
        bound["query_records"] = query_records
        doc["bound"] = bound
        doc["updated_at"] = datetime.now(timezone.utc)
        upsert_group_chat(doc)

    return make_succ_response(doc)
