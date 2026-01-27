from flask import request

from wxcloudrun.api import api_bp
from wxcloudrun.response import make_err_response, make_succ_response
import config
from wxcloudrun.services.wecom.auth.web_oauth import build_oauth2_url, get_user_detail, get_user_info
from wxcloudrun.services.wecom_client import WeComApiError


@api_bp.route("/suite/oauth2_url", methods=["GET"])
def api_suite_oauth2_url():
    """前端调用：构造第三方应用 OAuth2 授权链接。"""
    redirect_uri = request.args.get("redirect_uri") or config.WXWORK_OAUTH_REDIRECT
    if not redirect_uri:
        return make_err_response("redirect_uri is required")
    scope = request.args.get("scope", "snsapi_privateinfo")
    state = request.args.get("state", "STATE")
    try:
        url = build_oauth2_url(redirect_uri, scope=scope, state=state, appid=config.WXWORK_CORP_ID)
        return make_succ_response({"url": url})
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@api_bp.route("/suite/getuserinfo3rd", methods=["GET", "POST"])
def api_suite_getuserinfo3rd():
    """前端调用：通过 code 获取第三方临时用户信息。"""
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


@api_bp.route("/suite/getuserdetail3rd", methods=["POST"])
def api_suite_getuserdetail3rd():
    """前端调用：通过 user_ticket 获取成员敏感信息。"""
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