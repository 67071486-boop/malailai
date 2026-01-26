"""企业授权 / corp_token 相关 API。

封装获取企业 access_token 的流程：使用 suite_access_token + permanent_code
向企业微信换取对应企业的 `access_token`。获取后可通过 `CorpTokenProvider` 缓存。
"""
from typing import Any, Dict
from .base import BaseClient, WeComApiError
from wxcloudrun.services import token_cache


class CorpAuthApi(BaseClient):
    def __init__(self, session=None, timeout: int = 10):
        super().__init__(session=session, timeout=timeout)

    def get_corp_token(self, suite_id: str, corp_id: str, permanent_code: str) -> Dict[str, Any]:
        """使用 suite_access_token 与 permanent_code 向企业微信申请企业 access_token。

        返回包含 `access_token` 与 `expires_in`。
        """
        suite_token = token_cache.get_suite_access_token()
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
) -> Dict[str, Any]:
    client = CorpAuthApi(session=session, timeout=timeout)
    data = client.get_corp_token(suite_id, corp_id, permanent_code)
    access_token = data.get("access_token")
    if not access_token:
        raise WeComApiError("missing access_token in response")
    expires_in = int(data.get("expires_in", 7200))
    # 保存企业 access_token 以便后续接口调用使用
    token_cache.save_corp_token(corp_id, access_token, expires_in)
    return data
