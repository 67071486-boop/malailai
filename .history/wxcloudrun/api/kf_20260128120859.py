from flask import request

from wxcloudrun.api import api_bp
from wxcloudrun.api.helpers import (
    _as_list,
    _missing_token_response,
    _normalize_int_list,
    _require_str_param,
    _resolve_access_token,
)
from wxcloudrun.response import make_err_response, make_succ_response
from wxcloudrun.services.wecom.kf.account_manager import KfAccountApi
from wxcloudrun.services.wecom.kf.servicer_manager import KfStaffApi
from wxcloudrun.services.wecom_client import WeComApiError

kf_account_api = KfAccountApi()
kf_staff_api = KfStaffApi()


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
        return make_succ_response(data)
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
        return make_succ_response(data)
    except ValueError as exc:
        return make_err_response(str(exc))
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))