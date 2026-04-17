import logging
from typing import Optional, Dict, Any

from wecom import dao
from wecom.services.wecom.base import BaseClient, WeComApiError
import config

# 企微自建应用配置（从环境变量读取）
WXWORK_CORP_ID = config.WXWORK_CORP_ID
WXWORK_TOKEN = config.WXWORK_TOKEN
WXWORK_ENCODING_AES_KEY = config.WXWORK_ENCODING_AES_KEY
WXWORK_AGENT_SECRET = getattr(config, "WXWORK_AGENT_SECRET", "")


def save_corp_access_token(corp_id: str, token: str, expires_in: int) -> None:
    dao.save_corp_access_token(corp_id, token, expires_in)


def get_corp_access_token_cached(corp_id: str) -> Optional[str]:
    return dao.get_corp_access_token(corp_id)


def save_jsapi_ticket(
    corp_id: str, ticket: str, expires_in: int, *, ticket_type: str = "corp", agent_id: Optional[str] = None
) -> None:
    dao.save_jsapi_ticket(corp_id, ticket, expires_in, ticket_type=ticket_type, agent_id=agent_id)


def get_jsapi_ticket_cached(corp_id: str, *, ticket_type: str = "corp", agent_id: Optional[str] = None) -> Optional[str]:
    return dao.get_jsapi_ticket(corp_id, ticket_type=ticket_type, agent_id=agent_id)


def fetch_internal_corp_access_token(
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    """调用 gettoken 拉取自建应用 access_token 并写入缓存。"""
    if not WXWORK_CORP_ID or not WXWORK_AGENT_SECRET:
        raise WeComApiError("missing WXWORK_CORP_ID or WXWORK_AGENT_SECRET")
    client = BaseClient(session=session, timeout=timeout)
    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    data = client._do_get(url, params={"corpid": WXWORK_CORP_ID, "corpsecret": WXWORK_AGENT_SECRET})
    BaseClient._raise_if_errcode(data, "gettoken", required_keys=["access_token", "expires_in"])
    access_token = data.get("access_token")
    if not access_token:
        raise WeComApiError("missing access_token in gettoken response")
    expires_in = int(data.get("expires_in", 7200))
    save_corp_access_token(WXWORK_CORP_ID, str(access_token), expires_in)
    return data


def fetch_jsapi_ticket(
    access_token: str,
    corp_id: str,
    *,
    ticket_type: str = "corp",
    agent_id: Optional[str] = None,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    client = BaseClient(session=session, timeout=timeout)
    if ticket_type == "agent":
        url = "https://qyapi.weixin.qq.com/cgi-bin/ticket/get"
        params = {"access_token": access_token, "type": "agent_config"}
        data = client._do_get(url, params=params)
        BaseClient._raise_if_errcode(data, "fetch_agent_jsapi_ticket", required_keys=["ticket", "expires_in"])
    else:
        url = "https://qyapi.weixin.qq.com/cgi-bin/get_jsapi_ticket"
        params = {"access_token": access_token}
        data = client._do_get(url, params=params)
        BaseClient._raise_if_errcode(data, "fetch_corp_jsapi_ticket", required_keys=["ticket", "expires_in"])

    ticket = data.get("ticket")
    if not ticket:
        raise WeComApiError("missing jsapi_ticket in response")
    expires_in = int(data.get("expires_in", 7200))
    save_jsapi_ticket(corp_id, str(ticket), expires_in, ticket_type=ticket_type, agent_id=agent_id)
    return data


def get_corp_access_token(
    corp_id: str,
    permanent_code: Optional[str] = None,
    force_refresh: bool = False,
) -> Optional[str]:
    """获取企业 access_token（自建应用 gettoken，带缓存）。

    `permanent_code` 已废弃，仅保留参数以兼容旧调用。
    单企业场景下始终使用环境变量中的 corpid + 应用 Secret。
    """
    canonical = WXWORK_CORP_ID
    if not canonical:
        return None
    if corp_id and corp_id != canonical:
        logging.getLogger("wecom.token_service").warning(
            "corp_id=%s 与 WXWORK_CORP_ID 不一致，仍使用配置的企业 ID 获取 access_token",
            corp_id,
        )
    if not force_refresh:
        token = get_corp_access_token_cached(canonical)
        if token:
            return token
    try:
        fetch_internal_corp_access_token()
        return get_corp_access_token_cached(canonical)
    except Exception:
        logging.getLogger("wecom.token_service").exception("get_corp_access_token failed")
        return None


__all__ = [
    "WXWORK_CORP_ID",
    "WXWORK_TOKEN",
    "WXWORK_ENCODING_AES_KEY",
    "save_corp_access_token",
    "get_corp_access_token_cached",
    "save_jsapi_ticket",
    "get_jsapi_ticket_cached",
    "fetch_internal_corp_access_token",
    "fetch_jsapi_ticket",
    "get_corp_access_token",
]
