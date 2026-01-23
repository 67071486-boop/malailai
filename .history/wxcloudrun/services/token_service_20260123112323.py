import os
import time
import logging
from typing import Optional
from wxcloudrun.services import token_cache
from wxcloudrun.services import wecom_client

# 企微配置（全部从环境变量读取）
WXWORK_CORP_ID = os.getenv("WXWORK_CORP_ID", "your_corp_id")
WXWORK_TOKEN = os.getenv("WXWORK_TOKEN", "your_token")
WXWORK_ENCODING_AES_KEY = os.getenv("WXWORK_ENCODING_AES_KEY", "your_aes_key")
WXWORK_SUITE_ID = os.getenv("WXWORK_SUITE_ID", "your_suite_id")
WXWORK_SUITE_SECRET = os.getenv("WXWORK_SUITE_SECRET", "your_suite_secret")

# 现在使用独立的 token_cache 保存 token，wecom_client 提供用于拉取 token 的低级 fetch 方法


def save_suite_ticket(ticket: str) -> None:
    """保存 suite_ticket 到缓存。"""
    token_cache.save_suite_ticket(ticket)


def get_suite_ticket() -> Optional[str]:
    return token_cache.get_suite_ticket()


def get_suite_access_token() -> Optional[str]:
    """获取第三方应用 suite_access_token（带缓存）。

    若缓存不存在则使用 `wecom_client.fetch_suite_access_token` 主动拉取并保存。
    """
    token = token_cache.get_suite_access_token()
    if token:
        return token

    ticket = token_cache.get_suite_ticket()
    if not ticket:
        return None

    try:
        # wecom_client.fetch_suite_access_token 会把结果写入 token_cache
        wecom_client.fetch_suite_access_token(ticket, WXWORK_SUITE_ID, WXWORK_SUITE_SECRET)
        return token_cache.get_suite_access_token()
    except Exception:
        logging.getLogger("wxcloudrun.token_service").exception(
            "get_suite_access_token failed for ticket=%s", ticket
        )
        return None


def get_corp_access_token(corp_id: str, permanent_code: str) -> Optional[str]:
    """根据 corp_id/permanent_code 获取企业 access_token（带缓存）。

    若缓存不存在则使用 `wecom_client.fetch_corp_access_token` 拉取并保存。
    """
    token = token_cache.get_corp_token(corp_id)
    if token:
        return token

    try:
        wecom_client.fetch_corp_access_token(corp_id, permanent_code, WXWORK_SUITE_ID)
        return token_cache.get_corp_token(corp_id)
    except Exception:
        logging.getLogger("wxcloudrun.token_service").exception(
            "Exception while get_corp_access_token for corp_id=%s", corp_id
        )
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
