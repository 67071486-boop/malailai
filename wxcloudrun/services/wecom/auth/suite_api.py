"""第三方应用（Suite）相关 API。

封装 Suite 相关的常用调用，如获取 `suite_access_token`、永久授权码。
"""
from typing import Any, Dict, Optional
from ..base import BaseClient, WeComApiError
from wxcloudrun.services import token_service


class SuiteApi(BaseClient):
    def __init__(self, session=None, timeout: int = 10):
        super().__init__(session=session, timeout=timeout)

    def get_suite_access_token(self) -> Optional[str]:
        """从缓存获取 `suite_access_token`。"""
        return token_service.get_suite_access_token_cached()

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
