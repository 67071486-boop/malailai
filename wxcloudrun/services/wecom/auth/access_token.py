"""第三方应用 access_token 相关 API。

包含：
- Suite access_token 与永久授权码（SuiteApi）
- 企业 access_token 获取（CorpAuthApi）
"""
from typing import Any, Dict, Optional

from ..base import BaseClient, WeComApiError
from wxcloudrun.services.service import token_service


class SuiteApi(BaseClient):
    def __init__(self, session=None, timeout: int = 10):
        super().__init__(session=session, timeout=timeout)

    def get_suite_access_token(self) -> Optional[str]:
        """从缓存获取 `suite_access_token`。"""
        return token_service.get_suite_access_token_cached()

    def get_permanent_code(self, auth_code: str) -> Dict[str, Any]:
        """通过 `auth_code` 申请 `permanent_code` 和企业信息。"""
        token = self.get_suite_access_token()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_permanent_code"
        data = self._do_post(url + f"?suite_access_token={token}", json={"auth_code": auth_code})
        self._raise_if_errcode(data, "get_permanent_code", required_keys=["permanent_code", "auth_corp_info"])
        return data


class CorpAuthApi(BaseClient):
    def __init__(self, session=None, timeout: int = 10):
        super().__init__(session=session, timeout=timeout)

    def get_corp_token(self, suite_id: str, corp_id: str, permanent_code: str) -> Dict[str, Any]:
        """使用 suite_access_token 与 permanent_code 申请企业 access_token。"""
        suite_token = token_service.get_suite_access_token_cached()
        if not suite_token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_corp_token"
        payload = {"auth_corpid": corp_id, "permanent_code": permanent_code, "suite_id": suite_id}
        data = self._do_post(url + f"?suite_access_token={suite_token}", json=payload)
        self._raise_if_errcode(data, "get_corp_token", required_keys=["access_token", "expires_in"])
        return data


def fetch_suite_access_token(
    ticket: str,
    suite_id: str,
    suite_secret: str,
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    return token_service.fetch_suite_access_token(
        ticket,
        suite_id,
        suite_secret,
        session=session,
        timeout=timeout,
    )


def fetch_corp_access_token(
    corp_id: str,
    permanent_code: str,
    suite_id: str,
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    return token_service.fetch_corp_access_token(
        corp_id,
        permanent_code,
        suite_id,
        session=session,
        timeout=timeout,
    )
