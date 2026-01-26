"""企业授权 / corp_token 相关 API。

封装获取企业 access_token 的流程：使用 suite_access_token + permanent_code
向企业微信换取对应企业的 `access_token`。获取后可通过 `CorpTokenProvider` 缓存。
"""
from typing import Any, Dict, Optional
from .base import BaseClient, WeComApiError
from .token_provider import SuiteTokenProvider, CorpTokenProvider


class CorpAuthApi(BaseClient):
    def __init__(
        self,
        session=None,
        timeout: int = 10,
        suite_token_provider: Optional[SuiteTokenProvider] = None,
        corp_token_provider: Optional[CorpTokenProvider] = None,
    ):
        super().__init__(session=session, timeout=timeout)
        self.suite_token_provider = suite_token_provider or SuiteTokenProvider()
        self.corp_token_provider = corp_token_provider or CorpTokenProvider()

    def get_corp_token(self, suite_id: str, corp_id: str, permanent_code: str) -> Dict[str, Any]:
        """使用 suite_access_token 与 permanent_code 向企业微信申请企业 access_token。

        返回包含 `access_token` 与 `expires_in`。
        """
        suite_token = self.suite_token_provider.get_suite_access_token()
        if not suite_token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_corp_token"
        payload = {"auth_corpid": corp_id, "permanent_code": permanent_code, "suite_id": suite_id}
        data = self._do_post(url + f"?suite_access_token={suite_token}", json=payload)
        self._raise_if_errcode(data, "get_corp_token", required_keys=["access_token", "expires_in"])
        return data


def fetch_corp_access_token(
    corp_id: str,
    permanent_code: str,
    suite_id: str,
    *,
    session=None,
    timeout: int = 10,
    suite_token_provider: Optional[SuiteTokenProvider] = None,
    corp_token_provider: Optional[CorpTokenProvider] = None,
) -> Dict[str, Any]:
    suite_provider = suite_token_provider or SuiteTokenProvider()
    corp_provider = corp_token_provider or CorpTokenProvider()
    client = CorpAuthApi(
        session=session,
        timeout=timeout,
        suite_token_provider=suite_provider,
        corp_token_provider=corp_provider,
    )
    data = client.get_corp_token(suite_id, corp_id, permanent_code)
    access_token = data.get("access_token")
    if not access_token:
        raise WeComApiError("missing access_token in response")
    expires_in = int(data.get("expires_in", 7200))
    # 保存企业 access_token 以便后续接口调用使用
    corp_provider.save_corp_access_token(corp_id, access_token, expires_in)
    return data
