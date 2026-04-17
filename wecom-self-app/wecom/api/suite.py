from flask import request

from wecom.api import api_bp
from wecom.response import make_err_response, make_succ_response
import config
from wecom.services.wecom.auth.web_oauth import build_oauth2_url, get_user_detail, get_user_info
from wecom.services.wecom_client import WeComApiError


@api_bp.route("/suite/oauth2_url", methods=["GET"])
def api_suite_oauth2_url():
    """前端调用：构造自建应用 OAuth2 授权链接（路径保留 /suite 以兼容旧前端）。"""
    redirect_uri = request.args.get("redirect_uri") or config.WXWORK_OAUTH_REDIRECT
    if not redirect_uri:
        return make_err_response("redirect_uri is required")
    scope = request.args.get("scope", "snsapi_privateinfo")
    state = request.args.get("state", "STATE")
    try:
        url = build_oauth2_url(
            redirect_uri,
            scope=scope,
            state=state,
            appid=config.WXWORK_CORP_ID,
            agent_id=config.WXWORK_AGENT_ID or None,
        )
        return make_succ_response({"url": url})
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@api_bp.route("/suite/getuserinfo3rd", methods=["GET", "POST"])
def api_suite_getuserinfo3rd():
    """前端调用：通过 code 获取成员身份（自建应用 auth/getuserinfo；路径名保留）。"""
    params = request.get_json(silent=True) or {}
    code = params.get("code") or request.args.get("code")
    if not code:
        return make_err_response("code is required")

    try:
        data = get_user_info(code)
        return make_succ_response(data)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@api_bp.route("/suite/getuserdetail3rd", methods=["GET", "POST"])
def api_suite_getuserdetail3rd():
    """前端调用：通过 user_ticket 获取成员敏感信息（自建应用 auth/getuserdetail）。"""
    params = request.get_json(silent=True) or {}
    user_ticket = params.get("user_ticket") or request.args.get("user_ticket")
    if not user_ticket:
        return make_err_response("user_ticket is required")

    try:
        data = get_user_detail(user_ticket)
        return make_succ_response(data)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))
