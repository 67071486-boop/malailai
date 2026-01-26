"""Token 提供与缓存适配层。

该模块封装了对全局内存 token 缓存（`token_cache`）的访问，
为上层 API 提供统一的读取/写入接口：
- `SuiteTokenProvider`：处理 suite 级别的 ticket 与 suite_access_token
- `CorpTokenProvider`：处理企业（corp）级别的 access_token

在生产环境中，可替换为使用 Redis 或其他持久化缓存的实现。
"""
from typing import Optional
from wxcloudrun.services import token_cache


class SuiteTokenProvider:
    def get_suite_access_token(self) -> Optional[str]:
        """获取缓存中的 `suite_access_token`，不存在时返回 None。"""
        return token_cache.get_suite_access_token()

    def save_suite_access_token(self, token: str, expires_in: int) -> None:
        """保存 `suite_access_token` 到缓存，`expires_in` 为秒数。"""
        token_cache.save_suite_access_token(token, expires_in)

    def get_suite_ticket(self) -> Optional[str]:
        """获取最新的 `suite_ticket`（企业微信推送），用于换取 suite_access_token。"""
        return token_cache.get_suite_ticket()

    def save_suite_ticket(self, ticket: str) -> None:
        """保存 `suite_ticket` 到缓存（通常由企业微信回调推送）。"""
        token_cache.save_suite_ticket(ticket)


class CorpTokenProvider:
    def get_corp_access_token(self, corp_id: str) -> Optional[str]:
        """从缓存获取指定 `corp_id` 的企业 access_token。"""
        return token_cache.get_corp_token(corp_id)

    def save_corp_access_token(self, corp_id: str, token: str, expires_in: int) -> None:
        """保存企业 access_token 到缓存，供后续接口调用使用。"""
        token_cache.save_corp_token(corp_id, token, expires_in)
