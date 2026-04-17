"""自建应用 access_token 通过 token_service.fetch_internal_corp_access_token（gettoken）获取。

本文件保留 CorpAuthApi 等薄封装，便于旧代码迁移。
"""
from typing import Any, Dict, Optional

from ..base import BaseClient, WeComApiError
from wecom.services.service import token_service


class CorpAuthApi(BaseClient):
    def __init__(self, session=None, timeout: int = 10):
        super().__init__(session=session, timeout=timeout)

    def get_corp_token(self, suite_id: str, corp_id: str, permanent_code: str) -> Dict[str, Any]:
        """兼容旧签名：实际调用自建应用 gettoken。"""
        del suite_id, permanent_code
        return token_service.fetch_internal_corp_access_token(session=self.session, timeout=self.timeout)


def fetch_corp_access_token(
    corp_id: str,
    permanent_code: str,
    suite_id: str,
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    del corp_id, permanent_code, suite_id
    return token_service.fetch_internal_corp_access_token(session=session, timeout=timeout)
