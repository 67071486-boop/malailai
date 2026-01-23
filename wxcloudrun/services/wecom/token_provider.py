"""Token 提供与缓存适配层。"""
from typing import Optional
from wxcloudrun.services import token_cache


class SuiteTokenProvider:
    def get_suite_access_token(self) -> Optional[str]:
        return token_cache.get_suite_access_token()

    def save_suite_access_token(self, token: str, expires_in: int) -> None:
        token_cache.save_suite_access_token(token, expires_in)

    def get_suite_ticket(self) -> Optional[str]:
        return token_cache.get_suite_ticket()

    def save_suite_ticket(self, ticket: str) -> None:
        token_cache.save_suite_ticket(ticket)


class CorpTokenProvider:
    def get_corp_access_token(self, corp_id: str) -> Optional[str]:
        return token_cache.get_corp_token(corp_id)

    def save_corp_access_token(self, corp_id: str, token: str, expires_in: int) -> None:
        token_cache.save_corp_token(corp_id, token, expires_in)
