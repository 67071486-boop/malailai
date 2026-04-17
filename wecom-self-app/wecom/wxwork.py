from urllib.parse import quote
from wecom.services.wecom_client import WeComApiError
from flask import Blueprint, request, redirect, url_for, session
from flask.typing import ResponseReturnValue
from wecom.services.service.callback_service import handle_wecom_callback
from wecom.services.service.token_service import get_corp_access_token
from wecom.services.wecom.auth.web_oauth import build_oauth2_url, get_user_info
from wecom.response import make_succ_response, make_err_response
import config

wxwork_bp = Blueprint("wxwork", __name__, url_prefix="/wxwork")

# 可选：默认重定向地址（需配置可信域名）
_DEFAULT_REDIRECT_URI = config.WXWORK_OAUTH_REDIRECT


@wxwork_bp.route("/callback", methods=["GET", "POST"])
def callback_message() -> ResponseReturnValue:
    """自建应用「接收消息」服务器 URL（企微后台仅支持填一个地址：`https://你的域名/wxwork/callback`）。"""
    print("[接收消息回调] ", request.method, flush=True)
    return handle_wecom_callback(request)


@wxwork_bp.route("/oauth/login", methods=["GET"])
def oauth_login():
    """构造 OAuth 授权链接并跳转，用于获取成员 code。"""
    redirect_uri = request.args.get("redirect_uri") or _DEFAULT_REDIRECT_URI
    if not redirect_uri:
        print("[wxwork] oauth_login 缺少 redirect_uri，请在参数或环境变量 WXWORK_OAUTH_REDIRECT 中配置", flush=True)
        return make_err_response("缺少 redirect_uri，请在参数或 WXWORK_OAUTH_REDIRECT 环境变量中配置")

    state = request.args.get("state", "STATE")
    login_url = build_oauth2_url(
        redirect_uri,
        scope="snsapi_privateinfo",
        state=state,
        appid=config.WXWORK_CORP_ID,
        agent_id=config.WXWORK_AGENT_ID or None,
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
        print("[wxwork] oauth_callback 未带 code，重定向到授权入口", flush=True)
        return redirect(login_url)

    access_token = get_corp_access_token(config.WXWORK_CORP_ID)
    if not access_token:
        print("[wxwork] oauth_callback 无法获取 access_token，请检查 WXWORK_AGENT_SECRET。code=", code, "args=", dict(request.args), flush=True)
        return make_err_response("无法获取 access_token，请检查 WXWORK_CORP_ID 与 WXWORK_AGENT_SECRET"), 500

    try:
        data = get_user_info(code)
    except WeComApiError as e:
        print("[wxwork] auth/getuserinfo WeCom API 错误:", e, "code=", code, flush=True)
        return make_err_response(f"auth/getuserinfo 失败: {e}"), 500
    except Exception as exc:
        import traceback

        print("[wxwork] 调用 auth/getuserinfo 异常 code=", code, "exc=", exc, flush=True)
        traceback.print_exc()
        return make_err_response(f"调用 auth/getuserinfo 异常: {exc}"), 500

    # 将用户信息写入 session（如果已配置 SECRET_KEY）
    try:
        session["wx_user"] = data
    except Exception:
        print("[wxwork] 写入 session 失败，请确认 SECRET_KEY 已配置", flush=True)

    print("[wxwork] oauth_callback 成功 user_info keys=", list(data.keys()), "state=", state, flush=True)
    payload = {"state": state, "user_info": data}
    return make_succ_response(payload)
