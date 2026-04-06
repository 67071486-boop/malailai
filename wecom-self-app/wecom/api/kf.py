from flask import request

from wecom.api import api_bp
from wecom.api.helpers import (
    _as_list,
    _missing_token_response,
    _normalize_int_list,
    _require_str_param,
    _resolve_access_token,
)
from wecom.dao import query_kf_welcome, upsert_kf_welcome
from wecom.model import new_kf_welcome
from wecom.response import make_err_response, make_succ_response
from wecom.services.wecom.kf.account_manager import KfAccountApi
from wecom.services.wecom.kf.servicer_manager import KfStaffApi
from wecom.services.wecom_client import WeComApiError

kf_account_api = KfAccountApi()
kf_staff_api = KfStaffApi()


def _utf8_len(value: str) -> int:
    return len(value.encode("utf-8"))


def _require_str_field(obj, key, *, min_bytes=1, max_bytes=None):
    value = obj.get(key)
    if not isinstance(value, str):
        return None, f"{key} must be a string"
    if not value.strip():
        return None, f"{key} cannot be empty"
    length = _utf8_len(value)
    if min_bytes is not None and length < min_bytes:
        return None, f"{key} too short"
    if max_bytes is not None and length > max_bytes:
        return None, f"{key} too long"
    return value, None


def _validate_msgmenu(msgmenu):
    if not isinstance(msgmenu, dict):
        return "msgmenu must be an object"
    head = msgmenu.get("head_content")
    if head is not None:
        if not isinstance(head, str):
            return "msgmenu.head_content must be a string"
        if _utf8_len(head) > 1024:
            return "msgmenu.head_content too long"
    tail = msgmenu.get("tail_content")
    if tail is not None:
        if not isinstance(tail, str):
            return "msgmenu.tail_content must be a string"
        if _utf8_len(tail) > 1024:
            return "msgmenu.tail_content too long"

    items = msgmenu.get("list")
    if items is None:
        return None
    if not isinstance(items, list):
        return "msgmenu.list must be an array"
    if len(items) > 10:
        return "msgmenu.list too many items"

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            return f"msgmenu.list[{idx}] must be an object"
        item_type = item.get("type")
        if item_type not in {"click", "view", "miniprogram", "text"}:
            return f"msgmenu.list[{idx}].type invalid"
        if item_type == "click":
            click = item.get("click")
            if not isinstance(click, dict):
                return f"msgmenu.list[{idx}].click is required"
            _, err = _require_str_field(click, "content", min_bytes=1, max_bytes=128)
            if err:
                return f"msgmenu.list[{idx}].click.content {err}"
            if "id" in click and click.get("id") is not None:
                _, err = _require_str_field(click, "id", min_bytes=1, max_bytes=128)
                if err:
                    return f"msgmenu.list[{idx}].click.id {err}"
        elif item_type == "view":
            view = item.get("view")
            if not isinstance(view, dict):
                return f"msgmenu.list[{idx}].view is required"
            _, err = _require_str_field(view, "url", min_bytes=1, max_bytes=2048)
            if err:
                return f"msgmenu.list[{idx}].view.url {err}"
            _, err = _require_str_field(view, "content", min_bytes=1, max_bytes=1024)
            if err:
                return f"msgmenu.list[{idx}].view.content {err}"
        elif item_type == "miniprogram":
            mini = item.get("miniprogram")
            if not isinstance(mini, dict):
                return f"msgmenu.list[{idx}].miniprogram is required"
            _, err = _require_str_field(mini, "appid", min_bytes=1, max_bytes=32)
            if err:
                return f"msgmenu.list[{idx}].miniprogram.appid {err}"
            _, err = _require_str_field(mini, "pagepath", min_bytes=1, max_bytes=1024)
            if err:
                return f"msgmenu.list[{idx}].miniprogram.pagepath {err}"
            if "content" in mini and mini.get("content") is not None:
                _, err = _require_str_field(mini, "content", min_bytes=0, max_bytes=1024)
                if err:
                    return f"msgmenu.list[{idx}].miniprogram.content {err}"
        elif item_type == "text":
            text = item.get("text")
            if not isinstance(text, dict):
                return f"msgmenu.list[{idx}].text is required"
            _, err = _require_str_field(text, "content", min_bytes=1, max_bytes=256)
            if err:
                return f"msgmenu.list[{idx}].text.content {err}"
            if "no_newline" in text and text.get("no_newline") is not None:
                if not isinstance(text.get("no_newline"), (bool, int)):
                    return f"msgmenu.list[{idx}].text.no_newline invalid"
    return None


def _validate_menu_replies(menu_replies):
    if not isinstance(menu_replies, dict):
        return "menu_replies must be an object"
    if not menu_replies:
        return "menu_replies cannot be empty"
    for menu_id, reply in menu_replies.items():
        if not isinstance(menu_id, str) or not menu_id.strip():
            return "menu_replies key invalid"
        if _utf8_len(menu_id) > 128:
            return "menu_replies key too long"
        if not isinstance(reply, dict):
            return f"menu_replies[{menu_id}] must be an object"
        msgtype = reply.get("msgtype")
        if not isinstance(msgtype, str) or not msgtype.strip():
            return f"menu_replies[{menu_id}].msgtype is required"
        msgtype = msgtype.strip()
        if msgtype == "text":
            text = reply.get("text")
            if not isinstance(text, dict) or not isinstance(text.get("content"), str):
                return f"menu_replies[{menu_id}].text.content is required"
            if _utf8_len(text.get("content")) > 2048:
                return f"menu_replies[{menu_id}].text.content too long"
        elif msgtype == "msgmenu":
            msgmenu = reply.get("msgmenu")
            if not isinstance(msgmenu, dict):
                return f"menu_replies[{menu_id}].msgmenu is required"
            err = _validate_msgmenu(msgmenu)
            if err:
                return f"menu_replies[{menu_id}].msgmenu {err}"
        else:
            return f"menu_replies[{menu_id}].msgtype unsupported"
    return None


@api_bp.route("/kf/account/add", methods=["POST"])
def api_kf_account_add():
    """新增客服账号。"""
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return _missing_token_response()
    try:
        name = _require_str_param(params, "name")
        media_id = _require_str_param(params, "media_id")
        data = kf_account_api.add_account(access_token, name, media_id)
        return make_succ_response(data)
    except ValueError as exc:
        return make_err_response(str(exc))
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@api_bp.route("/kf/account/del", methods=["POST"])
def api_kf_account_del():
    """删除客服账号。"""
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return _missing_token_response()
    try:
        open_kfid = _require_str_param(params, "open_kfid")
        data = kf_account_api.delete_account(access_token, open_kfid)
        return make_succ_response(data)
    except ValueError as exc:
        return make_err_response(str(exc))
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@api_bp.route("/kf/account/update", methods=["POST"])
def api_kf_account_update():
    """更新客服账号（名称/头像）。"""
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return _missing_token_response()
    try:
        open_kfid = _require_str_param(params, "open_kfid")
        data = kf_account_api.update_account(
            access_token,
            open_kfid,
            name=params.get("name"),
            media_id=params.get("media_id"),
        )
        return make_succ_response(data)
    except ValueError as exc:
        return make_err_response(str(exc))
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@api_bp.route("/kf/account/list", methods=["POST"])
def api_kf_account_list():
    """获取客服账号列表。"""
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return _missing_token_response()
    try:
        offset = int(params.get("offset", 0) or 0)
        limit = int(params.get("limit", 20) or 20)
    except Exception:
        return make_err_response("offset/limit must be numbers")
    try:
        data = kf_account_api.list_accounts(access_token, offset=offset, limit=limit)
        return make_succ_response(data.get("account_list", data))
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@api_bp.route("/kf/account/contact_way", methods=["POST"])
def api_kf_account_contact_way():
    """获取客服账号的联系方式。"""
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return _missing_token_response()
    try:
        open_kfid = _require_str_param(params, "open_kfid")
        data = kf_account_api.get_contact_way(
            access_token,
            open_kfid,
            scene=params.get("scene"),
        )
        return make_succ_response(data.get("url", data))
    except ValueError as exc:
        return make_err_response(str(exc))
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@api_bp.route("/kf/servicer/list", methods=["POST"])
def api_kf_servicer_list():
    """获取客服接待人员列表。"""
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return _missing_token_response()
    try:
        open_kfid = _require_str_param(params, "open_kfid")
        data = kf_staff_api.list_staffs(access_token, open_kfid)
        return make_succ_response(data.get("servicer_list", data))
    except ValueError as exc:
        return make_err_response(str(exc))
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@api_bp.route("/kf/servicer/add", methods=["POST"])
def api_kf_servicer_add():
    """添加客服接待人员。"""
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return _missing_token_response()
    user_ids = _as_list(params.get("userid_list"))
    try:
        open_kfid = _require_str_param(params, "open_kfid")
        dept_ids = _normalize_int_list(params.get("department_id_list"))
        data = kf_staff_api.add_staffs(
            access_token,
            open_kfid,
            user_ids=user_ids,
            department_ids=dept_ids,
        )
        return data
    except ValueError as exc:
        return make_err_response(str(exc))
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@api_bp.route("/kf/servicer/del", methods=["POST"])
def api_kf_servicer_del():
    """删除客服接待人员。"""
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return _missing_token_response()
    user_ids = _as_list(params.get("userid_list"))
    try:
        open_kfid = _require_str_param(params, "open_kfid")
        dept_ids = _normalize_int_list(params.get("department_id_list"))
        data = kf_staff_api.del_staffs(
            access_token,
            open_kfid,
            user_ids=user_ids,
            department_ids=dept_ids,
        )
        return data
    except ValueError as exc:
        return make_err_response(str(exc))
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@api_bp.route("/kf/welcome/get", methods=["POST"])
def api_kf_welcome_get():
    """获取客服欢迎语配置。"""
    params = request.get_json() or {}
    try:
        corp_id = _require_str_param(params, "corp_id")
    except ValueError as exc:
        return make_err_response(str(exc))

    open_kfid = params.get("open_kfid")
    if open_kfid is not None:
        if not isinstance(open_kfid, str):
            return make_err_response("open_kfid must be a string")
        open_kfid = open_kfid.strip()
        if not open_kfid:
            return make_err_response("open_kfid cannot be empty")

    doc = query_kf_welcome(corp_id, open_kfid)
    if not doc and open_kfid:
        doc = query_kf_welcome(corp_id, None)
    if not doc:
        return make_err_response("welcome config not found")

    msgtype = doc.get("msgtype")
    payload = doc.get("payload")
    menu_replies = doc.get("menu_replies")
    if not isinstance(msgtype, str) or not isinstance(payload, dict):
        legacy = doc.get("welcome_reply")
        if isinstance(legacy, str) and legacy.strip():
            msgtype = "text"
            payload = {"content": legacy}

    if not isinstance(msgtype, str) or not isinstance(payload, dict):
        return make_err_response("welcome config invalid")

    data = {
        "corp_id": doc.get("corp_id"),
        "open_kfid": doc.get("open_kfid"),
        "msgtype": msgtype,
        msgtype: payload,
    }
    if isinstance(menu_replies, dict):
        data["menu_replies"] = menu_replies
    return make_succ_response(data)


@api_bp.route("/kf/welcome/set", methods=["POST"])
def api_kf_welcome_set():
    """设置客服欢迎语配置。"""
    params = request.get_json() or {}
    try:
        corp_id = _require_str_param(params, "corp_id")
    except ValueError as exc:
        return make_err_response(str(exc))

    open_kfid = params.get("open_kfid")
    if open_kfid is not None:
        if not isinstance(open_kfid, str):
            return make_err_response("open_kfid must be a string")
        open_kfid = open_kfid.strip()
        if not open_kfid:
            return make_err_response("open_kfid cannot be empty")

    msgtype = params.get("msgtype")
    if msgtype is None and "welcome_reply" in params:
        msgtype = "text"

    if not isinstance(msgtype, str) or not msgtype.strip():
        return make_err_response("msgtype is required")
    msgtype = msgtype.strip()

    payload = None
    menu_replies = None
    if msgtype == "text":
        text = params.get("text")
        if isinstance(text, dict) and isinstance(text.get("content"), str):
            content = text.get("content")
            if _utf8_len(content) > 2048:
                return make_err_response("text.content too long")
            payload = {"content": content}
        elif "welcome_reply" in params:
            reply = params.get("welcome_reply")
            if isinstance(reply, str) and reply.strip():
                if _utf8_len(reply) > 2048:
                    return make_err_response("text.content too long")
                payload = {"content": reply}
        if not payload:
            return make_err_response("text.content is required")
    elif msgtype == "msgmenu":
        msgmenu = params.get("msgmenu")
        if not isinstance(msgmenu, dict):
            return make_err_response("msgmenu is required")
        err = _validate_msgmenu(msgmenu)
        if err:
            return make_err_response(err)
        payload = msgmenu
        menu_replies = params.get("menu_replies")
        err = _validate_menu_replies(menu_replies)
        if err:
            return make_err_response(err)
    else:
        return make_err_response("unsupported msgtype")

    doc = new_kf_welcome(
        corp_id, msgtype, payload, open_kfid=open_kfid, menu_replies=menu_replies
    )
    upsert_kf_welcome(doc)
    data = {"corp_id": corp_id, "open_kfid": open_kfid, "msgtype": msgtype, msgtype: payload}
    if isinstance(menu_replies, dict):
        data["menu_replies"] = menu_replies
    return make_succ_response(data)