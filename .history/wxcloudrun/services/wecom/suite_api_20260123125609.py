"""第三方应用（Suite）相关 API。

封装 Suite 相关的常用调用，如获取 `suite_access_token`、永久授权码、
以及基于 suite 的临时用户信息查询（getuserinfo3rd）。
"""
from typing import Any, Dict, Optional
from .base import BaseClient, WeComApiError
from .token_provider import SuiteTokenProvider


class SuiteApi(BaseClient):
    def __init__(self, session=None, timeout: int = 10, token_provider: Optional[SuiteTokenProvider] = None):
        super().__init__(session=session, timeout=timeout)
        self.token_provider = token_provider or SuiteTokenProvider()

    def get_suite_access_token(self) -> Optional[str]:
        """从 `SuiteTokenProvider` 获取缓存的 `suite_access_token`。"""
        return self.token_provider.get_suite_access_token()

    def get_permanent_code(self, auth_code: str) -> Dict[str, Any]:
        """通过 `auth_code` 向企业微信申请 `permanent_code` 和企业信息。

        返回的数据包含 `permanent_code` 与 `auth_corp_info`（企业基本信息）。
        """
        token = self.get_suite_access_token()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_permanent_code"
        data = self._do_post(url + f"?suite_access_token={token}", json={"auth_code": auth_code})
        self._raise_if_errcode(data, "get_permanent_code", required_keys=["permanent_code", "auth_corp_info"])
        return data

    def getuserinfo3rd(self, code: str) -> Dict[str, Any]:
        """使用 `code`（企业授权后回调或前端得到的 code）查询第三方临时用户信息。

        该接口基于 suite_access_token 调用，会返回用户的 userid 等信息。
        """
        token = self.get_suite_access_token()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/getuserinfo3rd"
        data = self._do_get(url, params={"suite_access_token": token, "code": code})
        self._raise_if_errcode(data, "getuserinfo3rd")
        return data


def fetch_suite_access_token(
    ticket: str,
    suite_id: str,
    suite_secret: str,
    *,
    session=None,
    timeout: int = 10,
    token_provider: Optional[SuiteTokenProvider] = None,
) -> Dict[str, Any]:
    provider = token_provider or SuiteTokenProvider()
    client = BaseClient(session=session, timeout=timeout)
    url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_suite_token"
    payload = {"suite_id": suite_id, "suite_secret": suite_secret, "suite_ticket": ticket}
    data = client._do_post(url, json=payload)
    BaseClient._raise_if_errcode(data, "fetch_suite_access_token", required_keys=["suite_access_token", "expires_in"])
    token = data.get("suite_access_token")
    expires = int(data.get("expires_in", 7200))
    # 将获取到的 suite_access_token 缓存到 token_provider 中，方便后续调用复用
    provider.save_suite_access_token(token, expires)
    return data
