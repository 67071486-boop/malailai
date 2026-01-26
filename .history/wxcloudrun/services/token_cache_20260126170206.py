"""DB 持久化 token 缓存层。

职责：保存并读取 suite_ticket、suite_access_token、corp access token 的缓存与过期时间。
"""
from typing import Optional
from wxcloudrun import dao


def save_suite_ticket(ticket: str) -> None:
    dao.save_suite_ticket(ticket)


def get_suite_ticket() -> Optional[str]:
    return dao.get_suite_ticket()


def save_suite_access_token(token: str, expires_in: int) -> None:
    dao.save_suite_access_token(token, expires_in)


def get_suite_access_token() -> Optional[str]:
    return dao.get_suite_access_token()


def save_corp_token(corp_id: str, token: str, expires_in: int) -> None:
    dao.save_corp_access_token(corp_id, token, expires_in)


def get_corp_token(corp_id: str) -> Optional[str]:
    return dao.get_corp_access_token(corp_id)


__all__ = [
    "save_suite_ticket",
    "get_suite_ticket",
    "save_suite_access_token",
    "get_suite_access_token",
    "save_corp_token",
    "get_corp_token",
]
