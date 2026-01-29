"""第三方应用网页授权（身份验证）基础 API 封装。"""
from typing import Any, Dict, Optional
from urllib.parse import quote

import config
from wxcloudrun.services.service import token_service
from wxcloudrun.services.wecom.base import BaseClient, WeComApiError


def build_oauth2_url(
    redirect_uri: str,
    *,
    scope: str = "snsapi_privateinfo",
    state: str = "STATE",
    appid: Optional[str] = None,
) -> str:
    """构造第三方应用 OAuth2 授权链接。"""
    appid = appid or config.WXWORK_SUITE_ID
    if not appid:
        raise WeComApiError("missing suite_id for oauth2 url")
    if not redirect_uri:
        raise WeComApiError("redirect_uri is required")
    encoded_redirect = quote(redirect_uri, safe="")
    return (
        "https://open.weixin.qq.com/connect/oauth2/authorize?"
        f"appid={appid}&redirect_uri={encoded_redirect}&response_type=code&"
        f"scope={scope}&state={state}#wechat_redirect"
    )


class WebOAuthApi(BaseClient):
    """第三方应用网页授权接口封装。"""

    def __init__(self, session=None, timeout: int = 10):
        super().__init__(session=session, timeout=timeout)

    def get_user_info(self, code: str) -> Dict[str, Any]:
        """通过 code 获取第三方临时用户身份信息。"""
        token = token_service.get_suite_access_token()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/auth/getuserinfo3rd"
        data = self._do_get(url, params={"suite_access_token": token, "code": code})
        self._raise_if_errcode(data, "getuserinfo3rd")
        return data

    def get_user_detail(self, user_ticket: str) -> Dict[str, Any]:
        """通过 user_ticket 获取用户敏感信息。"""
        token = token_service.get_suite_access_token()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/auth/getuserdetail3rd"
        data = self._do_post(url + f"?suite_access_token={token}", json={"user_ticket": user_ticket})
        self._raise_if_errcode(data, "getuserdetail3rd")
        return data


def get_user_info(code: str) -> Dict[str, Any]:
    return WebOAuthApi().get_user_info(code)


def get_user_detail(user_ticket: str) -> Dict[str, Any]:
    return WebOAuthApi().get_user_detail(user_ticket)