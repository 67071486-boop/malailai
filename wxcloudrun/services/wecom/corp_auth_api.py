"""企业授权 / corp_token 相关 API。"""
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
    corp_provider.save_corp_access_token(corp_id, data.get("access_token"), int(data.get("expires_in", 7200)))
    return data
