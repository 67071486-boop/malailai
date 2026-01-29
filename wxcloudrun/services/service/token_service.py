import logging
from typing import Optional, Dict, Any
from wxcloudrun import dao
from wxcloudrun.services.wecom.base import BaseClient, WeComApiError
import config

# 企微配置（全部从环境变量读取）
WXWORK_CORP_ID = config.WXWORK_CORP_ID
WXWORK_TOKEN = config.WXWORK_TOKEN
WXWORK_ENCODING_AES_KEY = config.WXWORK_ENCODING_AES_KEY
WXWORK_SUITE_ID = config.WXWORK_SUITE_ID
WXWORK_SUITE_SECRET = config.WXWORK_SUITE_SECRET
WXWORK_PROVIDER_SECRET = config.WXWORK_PROVIDER_SECRET

# token_service 负责：缓存读写（DB）+ 缺失时的拉取刷新


def save_suite_ticket(ticket: str) -> None:
    dao.save_suite_ticket(ticket)


def get_suite_ticket() -> Optional[str]:
    return dao.get_suite_ticket()


def save_suite_access_token(token: str, expires_in: int) -> None:
    dao.save_suite_access_token(token, expires_in)


def get_suite_access_token_cached() -> Optional[str]:
    return dao.get_suite_access_token()


def save_corp_access_token(corp_id: str, token: str, expires_in: int) -> None:
    dao.save_corp_access_token(corp_id, token, expires_in)


def save_provider_access_token(token: str, expires_in: int) -> None:
    dao.save_provider_access_token(token, expires_in)


def save_jsapi_ticket(corp_id: str, ticket: str, expires_in: int, *, ticket_type: str = "corp", agent_id: Optional[str] = None) -> None:
    dao.save_jsapi_ticket(corp_id, ticket, expires_in, ticket_type=ticket_type, agent_id=agent_id)


def get_corp_access_token_cached(corp_id: str) -> Optional[str]:
    return dao.get_corp_access_token(corp_id)


def get_provider_access_token_cached() -> Optional[str]:
    return dao.get_provider_access_token()


def get_jsapi_ticket_cached(corp_id: str, *, ticket_type: str = "corp", agent_id: Optional[str] = None) -> Optional[str]:
    return dao.get_jsapi_ticket(corp_id, ticket_type=ticket_type, agent_id=agent_id)


def fetch_suite_access_token(
    ticket: str,
    suite_id: str,
    suite_secret: str,
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    client = BaseClient(session=session, timeout=timeout)
    url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_suite_token"
    payload = {"suite_id": suite_id, "suite_secret": suite_secret, "suite_ticket": ticket}
    data = client._do_post(url, json=payload)
    BaseClient._raise_if_errcode(data, "fetch_suite_access_token", required_keys=["suite_access_token", "expires_in"])
    token = data.get("suite_access_token")
    if not token:
        raise WeComApiError("missing suite_access_token in response")
    expires = int(data.get("expires_in", 7200))
    save_suite_access_token(str(token), expires)
    return data


def fetch_corp_access_token(
    corp_id: str,
    permanent_code: str,
    suite_id: str,
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    suite_token = get_suite_access_token()
    if not suite_token:
        raise WeComApiError("missing suite_access_token")
    client = BaseClient(session=session, timeout=timeout)
    url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_corp_token"
    payload = {"auth_corpid": corp_id, "permanent_code": permanent_code, "suite_id": suite_id}
    data = client._do_post(url + f"?suite_access_token={suite_token}", json=payload)
    BaseClient._raise_if_errcode(data, "get_corp_token", required_keys=["access_token", "expires_in"])
    access_token = data.get("access_token")
    if not access_token:
        raise WeComApiError("missing access_token in response")
    expires_in = int(data.get("expires_in", 7200))
    save_corp_access_token(corp_id, access_token, expires_in)
    return data


def fetch_provider_access_token(
    corp_id: str,
    provider_secret: str,
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    client = BaseClient(session=session, timeout=timeout)
    url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_provider_token"
    payload = {"corpid": corp_id, "provider_secret": provider_secret}
    data = client._do_post(url, json=payload)
    BaseClient._raise_if_errcode(
        data,
        "fetch_provider_access_token",
        required_keys=["provider_access_token", "expires_in"],
    )
    token = data.get("provider_access_token")
    if not token:
        raise WeComApiError("missing provider_access_token in response")
    expires_in = int(data.get("expires_in", 7200))
    save_provider_access_token(str(token), expires_in)
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


def get_suite_access_token(force_refresh: bool = False) -> Optional[str]:
    """获取第三方应用 suite_access_token（带缓存）。
    force_refresh=True 时跳过缓存，直接刷新。
    """
    if not force_refresh:
        token = get_suite_access_token_cached()
        if token:
            return token

    ticket = get_suite_ticket()
    if not ticket:
        return None

    try:
        fetch_suite_access_token(ticket, WXWORK_SUITE_ID, WXWORK_SUITE_SECRET)
        return get_suite_access_token_cached()
    except Exception:
        logging.getLogger("wxcloudrun.token_service").exception(
            "get_suite_access_token failed for ticket=%s", ticket
        )
        return None


def get_corp_access_token(corp_id: str, permanent_code: str, force_refresh: bool = False) -> Optional[str]:
    """根据 corp_id/permanent_code 获取企业 access_token（带缓存）。
    force_refresh=True 时跳过缓存，直接刷新。
    """
    if not force_refresh:
        token = get_corp_access_token_cached(corp_id)
        if token:
            return token

    try:
        fetch_corp_access_token(corp_id, permanent_code, WXWORK_SUITE_ID)
        return get_corp_access_token_cached(corp_id)
    except Exception:
        logging.getLogger("wxcloudrun.token_service").exception(
            "Exception while get_corp_access_token for corp_id=%s", corp_id
        )
        return None


def get_provider_access_token(force_refresh: bool = False) -> Optional[str]:
    """获取服务商 provider_access_token（带缓存）。
    force_refresh=True 时跳过缓存，直接刷新。
    """
    if not force_refresh:
        token = get_provider_access_token_cached()
        if token:
            return token

    if not WXWORK_CORP_ID or not WXWORK_PROVIDER_SECRET:
        return None

    try:
        fetch_provider_access_token(WXWORK_CORP_ID, WXWORK_PROVIDER_SECRET)
        return get_provider_access_token_cached()
    except Exception:
        logging.getLogger("wxcloudrun.token_service").exception(
            "get_provider_access_token failed for corp_id=%s", WXWORK_CORP_ID
        )
        return None


__all__ = [
    "WXWORK_CORP_ID",
    "WXWORK_TOKEN",
    "WXWORK_ENCODING_AES_KEY",
    "WXWORK_SUITE_ID",
    "save_suite_ticket",
    "get_suite_ticket",
    "save_suite_access_token",
    "get_suite_access_token_cached",
    "save_corp_access_token",
    "get_corp_access_token_cached",
    "save_provider_access_token",
    "get_provider_access_token_cached",
    "save_jsapi_ticket",
    "get_jsapi_ticket_cached",
    "fetch_suite_access_token",
    "fetch_corp_access_token",
    "fetch_provider_access_token",
    "fetch_jsapi_ticket",
    "get_suite_access_token",
    "get_corp_access_token",
    "get_provider_access_token",
]
