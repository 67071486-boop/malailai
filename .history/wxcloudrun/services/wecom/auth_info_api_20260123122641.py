"""获取企业授权信息（v2 接口）

接口文档：POST https://qyapi.weixin.qq.com/cgi-bin/service/v2/get_auth_info?suite_access_token=SUITE_ACCESS_TOKEN
请求体：{"auth_corpid": "auth_corpid_value", "permanent_code": "code_value"}
"""
from typing import Any, Dict, Optional
from .base import BaseClient, WeComApiError
from .token_provider import SuiteTokenProvider


class AuthInfoApi(BaseClient):
    def __init__(self, session=None, timeout: int = 10, token_provider: Optional[SuiteTokenProvider] = None):
        super().__init__(session=session, timeout=timeout)
        self.token_provider = token_provider or SuiteTokenProvider()

    def get_auth_info(self, auth_corpid: str, permanent_code: str) -> Dict[str, Any]:
        token = self.token_provider.get_suite_access_token()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/v2/get_auth_info"
        payload = {"auth_corpid": auth_corpid, "permanent_code": permanent_code}
        data = self._do_post(url + f"?suite_access_token={token}", json=payload)
        # auth_corp_info 是必须项
        self._raise_if_errcode(data, "get_auth_info", required_keys=["auth_corp_info"])
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
    client = AuthInfoApi(session=session, timeout=timeout, token_provider=provider)
    data = client.get_auth_info(auth_corpid, permanent_code)
    return data
