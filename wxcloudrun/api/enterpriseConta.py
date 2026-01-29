from flask import request

from wxcloudrun.api import api_bp
from wxcloudrun.api.helpers import _require_str_param
from wxcloudrun.response import make_err_response, make_succ_response
from wxcloudrun.services.wecom.enterpriseContact import get_enterprise_contact_api
from wxcloudrun.services.wecom_client import WeComApiError


enterprise_contact_api = get_enterprise_contact_api()


def _optional_int(params, key):
    if key not in params or params.get(key) is None:
        return None
    value = params.get(key)
    try:
        return int(value)
    except Exception:
        raise ValueError(f"{key} must be a number")


@api_bp.route("/enterprise/contact/search", methods=["POST"])
def api_enterprise_contact_search():
    """通讯录单个搜索（服务商）。"""
    params = request.get_json() or {}
    try:
        auth_corpid = _require_str_param(params, "auth_corpid")
        query_word = _require_str_param(params, "query_word")
        data = enterprise_contact_api.search_contact(
            auth_corpid=auth_corpid,
            query_word=query_word,
            provider_access_token=params.get("provider_access_token"),
            query_type=_optional_int(params, "query_type"),
            query_range=_optional_int(params, "query_range"),
            agentid=_optional_int(params, "agentid"),
            limit=_optional_int(params, "limit"),
            full_match_field=_optional_int(params, "full_match_field"),
            cursor=params.get("cursor"),
        )
        return make_succ_response(data.get("query_result", data))
    except ValueError as exc:
        return make_err_response(str(exc))
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@api_bp.route("/enterprise/contact/batchsearch", methods=["POST"])
def api_enterprise_contact_batchsearch():
    """通讯录批量搜索（服务商）。"""
    params = request.get_json() or {}
    try:
        auth_corpid = _require_str_param(params, "auth_corpid")
        query_request_list = params.get("query_request_list")
        if not isinstance(query_request_list, list) or not query_request_list:
            raise ValueError("query_request_list must be a non-empty list")
        data = enterprise_contact_api.batch_search_contact(
            auth_corpid=auth_corpid,
            query_request_list=query_request_list,
            provider_access_token=params.get("provider_access_token"),
            agentid=_optional_int(params, "agentid"),
        )
        return make_succ_response(data.get("query_result_list", data))
    except ValueError as exc:
        return make_err_response(str(exc))
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@api_bp.route("/enterprise/contact/sort", methods=["POST"])
def api_enterprise_contact_sort():
    """通讯录 userid 排序（服务商）。"""
    params = request.get_json() or {}
    try:
        auth_corpid = _require_str_param(params, "auth_corpid")
        useridlist = params.get("useridlist")
        if not isinstance(useridlist, list) or not useridlist:
            raise ValueError("useridlist must be a non-empty list")
        sort_options = params.get("sort_options")
        if sort_options is not None and not isinstance(sort_options, list):
            raise ValueError("sort_options must be a list")
        data = enterprise_contact_api.sort_userid(
            auth_corpid=auth_corpid,
            useridlist=useridlist,
            provider_access_token=params.get("provider_access_token"),
            sort_options=sort_options,
        )
        return make_succ_response(data.get("useridlist", data))
    except ValueError as exc:
        return make_err_response(str(exc))
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))
