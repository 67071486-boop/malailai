"""简单的内存 token 缓存层，避免在 token 获取逻辑中产生循环依赖。

职责：保存并读取 suite_ticket、suite_access_token、corp access token 的缓存与过期时间。
此模块不依赖其他服务模块，仅提供纯数据读写接口。
"""
from typing import Optional, Dict
import time

# module-level in-memory cache
_suite_ticket: Optional[str] = None
_suite_access_token: Optional[str] = None
_suite_token_expires: float = 0.0

_corp_tokens: Dict[str, Dict] = {}


def save_suite_ticket(ticket: str) -> None:
    global _suite_ticket
    _suite_ticket = ticket


def get_suite_ticket() -> Optional[str]:
    return _suite_ticket


def save_suite_access_token(token: str, expires_in: int) -> None:
    global _suite_access_token, _suite_token_expires
    _suite_access_token = token
    _suite_token_expires = time.time() + expires_in - 300


def get_suite_access_token() -> Optional[str]:
    if _suite_access_token and time.time() < _suite_token_expires:
        return _suite_access_token
    return None


def save_corp_token(corp_id: str, token: str, expires_in: int) -> None:
    _corp_tokens[corp_id] = {"token": token, "expires_at": time.time() + expires_in - 300}


def get_corp_token(corp_id: str) -> Optional[str]:
    info = _corp_tokens.get(corp_id)
    if not info:
        return None
    if time.time() >= info.get("expires_at", 0):
        return None
    return info.get("token")


__all__ = [
    "save_suite_ticket",
    "get_suite_ticket",
    "save_suite_access_token",
    "get_suite_access_token",
    "save_corp_token",
    "get_corp_token",
]
