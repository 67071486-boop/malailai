"""自建应用网页授权（OAuth2）与成员身份接口。"""
from typing import Any, Dict, Optional
from urllib.parse import quote

import config
from wecom.services.service import token_service
from wecom.services.wecom.base import BaseClient, WeComApiError


def build_oauth2_url(
    redirect_uri: str,
    *,
    scope: str = "snsapi_privateinfo",
    state: str = "STATE",
    appid: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> str:
    """构造自建应用 OAuth2 授权链接（文档：构造网页授权链接）。"""
    corp_id = appid or config.WXWORK_CORP_ID
    if not corp_id:
        raise WeComApiError("missing WXWORK_CORP_ID for oauth2 url")
    if not redirect_uri:
        raise WeComApiError("redirect_uri is required")
    aid = agent_id if agent_id is not None else getattr(config, "WXWORK_AGENT_ID", None)
    if scope in ("snsapi_privateinfo", "snsapi_userinfo") and not (aid and str(aid).strip()):
        raise WeComApiError("snsapi_privateinfo/snsapi_userinfo 需要配置 WXWORK_AGENT_ID 并在链接中携带 agentid")
    encoded_redirect = quote(redirect_uri, safe="")
    base = (
        "https://open.weixin.qq.com/connect/oauth2/authorize?"
        f"appid={corp_id}&redirect_uri={encoded_redirect}&response_type=code&"
        f"scope={scope}&state={state}"
    )
    if aid is not None and str(aid).strip():
        base += f"&agentid={aid}"
    return base + "#wechat_redirect"


class WebOAuthApi(BaseClient):
    """自建应用网页授权接口封装。"""

    def __init__(self, session=None, timeout: int = 10):
        super().__init__(session=session, timeout=timeout)

    def get_user_info(self, code: str) -> Dict[str, Any]:
        """通过 code 获取成员身份（auth/getuserinfo）。"""
        cid = config.WXWORK_CORP_ID
        token = token_service.get_corp_access_token(cid)
        if not token:
            raise WeComApiError("missing access_token (请检查 WXWORK_CORP_ID / WXWORK_AGENT_SECRET)")
        url = "https://qyapi.weixin.qq.com/cgi-bin/auth/getuserinfo"
        data = self._do_get(url, params={"access_token": token, "code": code})
        self._raise_if_errcode(data, "auth.getuserinfo")
        return data

    def get_user_detail(self, user_ticket: str) -> Dict[str, Any]:
        """通过 user_ticket 获取成员敏感信息（auth/getuserdetail）。"""
        cid = config.WXWORK_CORP_ID
        token = token_service.get_corp_access_token(cid)
        if not token:
            raise WeComApiError("missing access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/auth/getuserdetail"
        data = self._do_post(url + f"?access_token={token}", json={"user_ticket": user_ticket})
        self._raise_if_errcode(data, "auth.getuserdetail")
        return data


def get_user_info(code: str) -> Dict[str, Any]:
    return WebOAuthApi().get_user_info(code)


def get_user_detail(user_ticket: str) -> Dict[str, Any]:
    return WebOAuthApi().get_user_detail(user_ticket)
