import os
import time
import requests
from typing import Optional, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential

# 企微配置（全部从环境变量读取）
WXWORK_CORP_ID = os.getenv("WXWORK_CORP_ID", "your_corp_id")
WXWORK_TOKEN = os.getenv("WXWORK_TOKEN", "your_token")
WXWORK_ENCODING_AES_KEY = os.getenv("WXWORK_ENCODING_AES_KEY", "your_aes_key")
WXWORK_SUITE_ID = os.getenv("WXWORK_SUITE_ID", "your_suite_id")
WXWORK_SUITE_SECRET = os.getenv("WXWORK_SUITE_SECRET", "your_suite_secret")

# 内存缓存（单进程）
_suite_ticket: Optional[str] = None
_suite_access_token: Optional[str] = None
_suite_token_expires: float = 0.0

_corp_tokens = {}


def save_suite_ticket(ticket: str) -> None:
    """保存 suite_ticket 到内存缓存。"""
    global _suite_ticket
    _suite_ticket = ticket


def get_suite_ticket() -> Optional[str]:
    """获取 suite_ticket。"""
    return _suite_ticket


def _suite_token_alive() -> bool:
    return bool(_suite_access_token) and time.time() < _suite_token_expires


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
def _fetch_suite_access_token(ticket: str) -> Tuple[str, int]:
    url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_suite_token"
    payload = {
        "suite_id": WXWORK_SUITE_ID,
        "suite_secret": WXWORK_SUITE_SECRET,
        "suite_ticket": ticket,
    }
    resp = requests.post(url, json=payload, timeout=10)
    data = resp.json()
    if data.get("errcode", 0) != 0:
        raise RuntimeError(f"fetch suite_access_token failed: {data}")
    return data["suite_access_token"], int(data.get("expires_in", 7200))


def get_suite_access_token() -> Optional[str]:
    """获取第三方应用 suite_access_token（带缓存）。"""
    global _suite_access_token, _suite_token_expires

    if _suite_token_alive():
        return _suite_access_token

    ticket = get_suite_ticket()
    if not ticket:
        return None

    try:
        token, expires_in = _fetch_suite_access_token(ticket)
        _suite_access_token = token
        _suite_token_expires = time.time() + expires_in - 300  # 提前5分钟过期
        return _suite_access_token
    except Exception:
        return None


def _corp_token_alive(corp_id: str) -> bool:
    token_info = _corp_tokens.get(corp_id)
    return bool(token_info) and time.time() < token_info["expires_at"]


def get_corp_access_token(corp_id: str, permanent_code: str) -> Optional[str]:
    """根据 corp_id/permanent_code 获取企业 access_token（带缓存）。"""
    if _corp_token_alive(corp_id):
        return _corp_tokens[corp_id]["token"]

    suite_token = get_suite_access_token()
    if not suite_token:
        return None

    url = (
        "https://qyapi.weixin.qq.com/cgi-bin/service/get_corp_token"
        f"?suite_access_token={suite_token}"
    )
    payload = {"auth_corpid": corp_id, "permanent_code": permanent_code}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if data.get("errcode", 0) != 0:
            return None
        token = data.get("access_token")
        expires_in = int(data.get("expires_in", 7200))
        _corp_tokens[corp_id] = {"token": token, "expires_at": time.time() + expires_in - 300}
        return token
    except Exception:
        return None


__all__ = [
    "WXWORK_CORP_ID",
    "WXWORK_TOKEN",
    "WXWORK_ENCODING_AES_KEY",
    "WXWORK_SUITE_ID",
    "save_suite_ticket",
    "get_suite_ticket",
    "get_suite_access_token",
    "get_corp_access_token",
]
