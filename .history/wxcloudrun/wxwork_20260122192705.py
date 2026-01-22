import logging
import os
from urllib.parse import quote
import requests
from flask import Blueprint, request, redirect, url_for, session
from wxcloudrun.services.callback_service import handle_data_callback, handle_command_callback
from wxcloudrun.services.token_service import WXWORK_SUITE_ID, get_suite_access_token
from wxcloudrun.response import make_succ_response, make_err_response

wxwork_bp = Blueprint("wxwork", __name__, url_prefix="/wxwork")

# 可选：默认重定向地址（需配置可信域名）
_DEFAULT_REDIRECT_URI = os.getenv("WXWORK_OAUTH_REDIRECT")


@wxwork_bp.route("/callback/data", methods=["GET", "POST"])
def callback_data():
    """企业微信数据回调，解密和分发由 callback_service 处理。"""
    return handle_data_callback(request)


@wxwork_bp.route("/callback/command", methods=["GET", "POST"])
def callback_command():
    """企业微信指令回调（suite_ticket、create_auth 等）。"""
    return handle_command_callback(request)


@wxwork_bp.route("/app", methods=["GET"])
def app_home():
    """应用主页入口。工作台打开应用应指向此地址。

    该路由会把请求重定向到 `/oauth/login` 并带上 `redirect_uri`（回调地址），
    企业微信在验证通过后会把成员 `code` 回调到 `redirect_uri`。
    """
    # 使用显式传参的 redirect_uri，或者使用环境变量默认，或回退到本服务的 oauth_callback
    redirect_uri = request.args.get("redirect_uri") or _DEFAULT_REDIRECT_URI or url_for("wxwork.oauth_callback", _external=True)
    state = request.args.get("state", "STATE")
    login_url = url_for("wxwork.oauth_login", _external=True) + "?redirect_uri=" + quote(redirect_uri, safe="") + "&state=" + state
    return redirect(login_url)


@wxwork_bp.route("/oauth/login", methods=["GET"])
def oauth_login():
    """构造 OAuth 授权链接并跳转，用于获取成员 code。"""
    redirect_uri = request.args.get("redirect_uri") or _DEFAULT_REDIRECT_URI
    if not redirect_uri:
        return make_err_response("缺少 redirect_uri，请在参数或 WXWORK_OAUTH_REDIRECT 环境变量中配置")

    state = request.args.get("state", "STATE")
    login_url = (
        "https://open.weixin.qq.com/connect/oauth2/authorize?"
        f"appid={WXWORK_SUITE_ID}&"
        f"redirect_uri={quote(redirect_uri, safe='')}&"
        "response_type=code&scope=snsapi_userinfo&"
        f"state={state}#wechat_redirect"
    )
    return redirect(login_url)


@wxwork_bp.route("/oauth/callback", methods=["GET"])
def oauth_callback():
    """接收成员授权 code，换取用户身份信息。"""
    code = request.args.get("code")
    state = request.args.get("state")
    if not code:
        # 未携带 code 的直接访问，重定向到授权入口引导用户
        redirect_uri = _DEFAULT_REDIRECT_URI or url_for("wxwork.oauth_callback", _external=True)
        login_url = url_for("wxwork.oauth_login", _external=True) + "?redirect_uri=" + quote(redirect_uri, safe="")
        return redirect(login_url)

    suite_token = get_suite_access_token()
    if not suite_token:
        logging.getLogger("wxcloudrun.wxwork").error(
            "oauth_callback missing suite_access_token; code=%s args=%s", code, dict(request.args)
        )
        return make_err_response("缺少 suite_ticket 或获取 suite_access_token 失败，请先确保回调已收到 suite_ticket"), 500

    try:
        resp = requests.get(
            "https://qyapi.weixin.qq.com/cgi-bin/service/getuserinfo3rd",
            params={"suite_access_token": suite_token, "code": code},
            timeout=10,
        )
        data = resp.json()
    except Exception as exc:
        logging.getLogger("wxcloudrun.wxwork").exception(
            "Exception calling getuserinfo3rd: %s code=%s", exc, code
        )
        return make_err_response(f"调用 getuserinfo3rd 异常: {exc}"), 500

    if data.get("errcode", 0) != 0:
        logging.getLogger("wxcloudrun.wxwork").error(
            "getuserinfo3rd returned error: %s code=%s", data, code
        )
        return make_err_response(f"getuserinfo3rd 失败: {data}"), 500

    # 将用户信息写入 session（如果已配置 SECRET_KEY）
    try:
        session["wx_user"] = data
    except Exception:
        logging.getLogger("wxcloudrun.wxwork").warning("Failed to write user info to session; ensure SECRET_KEY is set")

    payload = {"state": state, "user_info": data}
    return make_succ_response(payload)