"""应用授权（第三方应用）相关接口封装。

包含：获取 pre_auth_code、获取永久授权码（代理到 SuiteApi）、查询企业授权信息（代理到 AuthInfoApi）。
"""
from typing import Any, Dict, Optional
from .base import BaseClient, WeComApiError
from .token_provider import SuiteTokenProvider
from .suite_api import SuiteApi


class AppAuthApi(BaseClient):
    def __init__(self, session=None, timeout: int = 10, token_provider: Optional[SuiteTokenProvider] = None):
        super().__init__(session=session, timeout=timeout)
        self.token_provider = token_provider or SuiteTokenProvider()
        self._suite_api = SuiteApi(session=self.session, timeout=self.timeout, token_provider=self.token_provider)
        self._auth_info_api = AuthInfoApi(session=self.session, timeout=self.timeout, token_provider=self.token_provider)

    def get_pre_auth_code(self, suite_id: str) -> Dict[str, Any]:
        token = self.token_provider.get_suite_access_token()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_pre_auth_code"
        payload = {"suite_id": suite_id}
        data = self._do_post(url + f"?suite_access_token={token}", json=payload)
        self._raise_if_errcode(data, "get_pre_auth_code", required_keys=["pre_auth_code"])
        return data

    def get_permanent_code(self, auth_code: str) -> Dict[str, Any]:
        # delegate to SuiteApi for existing logic
        return self._suite_api.get_permanent_code(auth_code)

    def get_auth_info(self, auth_corpid: str, permanent_code: str) -> Dict[str, Any]:
        # Implement get_auth_info here (moved from auth_info_api)
        token = self.token_provider.get_suite_access_token()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/v2/get_auth_info"
        payload = {"auth_corpid": auth_corpid, "permanent_code": permanent_code}
        data = self._do_post(url + f"?suite_access_token={token}", json=payload)
        self._raise_if_errcode(data, "get_auth_info", required_keys=["auth_corp_info"])
        return data


def fetch_pre_auth_code(
    suite_id: str,
    *,
    session=None,
    timeout: int = 10,
    token_provider: Optional[SuiteTokenProvider] = None,
) -> Dict[str, Any]:
    provider = token_provider or SuiteTokenProvider()
    client = AppAuthApi(session=session, timeout=timeout, token_provider=provider)
    data = client.get_pre_auth_code(suite_id)
    return data


def fetch_auth_info(
    auth_corpid: str,
    permanent_code: str,
    *,
    session=None,
    timeout: int = 10,
    token_provider: Optional[SuiteTokenProvider] = None,
) -> Dict[str, Any]:
    provider = token_provider or SuiteTokenProvider()
    client = AppAuthApi(session=session, timeout=timeout, token_provider=provider)
    return client.get_auth_info(auth_corpid, permanent_code)
