"""WeCom API 按业务域拆分后的工厂与兼容入口。"""
import requests
from typing import Optional

from .base import BaseClient, WeComApiError
from .auth.access_token import CorpAuthApi, fetch_corp_access_token
from .auth.auth_code import AppAuthApi, fetch_pre_auth_code, fetch_auth_info, fetch_app_permissions, fetch_corp_token
from .agent import AgentApi, fetch_agent_detail, fetch_agent_list
from .auth.web_oauth import WebOAuthApi, build_oauth2_url
from .enterpriseContact import EnterpriseContactApi, get_enterprise_contact_api
from wecom.services.service import token_service
import config

_shared_session = requests.Session()


def get_corp_auth_api(session: Optional[requests.Session] = None) -> CorpAuthApi:
    return CorpAuthApi(session=session or _shared_session)


def get_agent_api(session: Optional[requests.Session] = None) -> AgentApi:
    return AgentApi(session=session or _shared_session)


def get_auth_info_api(session: Optional[requests.Session] = None) -> AppAuthApi:
    return AppAuthApi(session=session or _shared_session)


def get_app_auth_api(session: Optional[requests.Session] = None) -> AppAuthApi:
    return AppAuthApi(session=session or _shared_session)


def get_web_oauth_api(session: Optional[requests.Session] = None) -> WebOAuthApi:
    return WebOAuthApi(session=session or _shared_session)


class CorpClient:
    """兼容旧接口的组合客户端。"""

    def __init__(self, session: Optional[requests.Session] = None):
        self._auth_api = get_corp_auth_api(session)

    def get_corp_access_token(self, suite_id: str, corp_id: str, permanent_code: str):
        del suite_id, permanent_code
        cid = corp_id or config.WXWORK_CORP_ID
        return token_service.get_corp_access_token(cid)


def get_corp_client() -> CorpClient:
    return CorpClient()


__all__ = [
    "BaseClient",
    "WeComApiError",
    "CorpAuthApi",
    "AgentApi",
    "get_corp_client",
    "get_corp_auth_api",
    "get_agent_api",
    "get_auth_info_api",
    "get_app_auth_api",
    "fetch_auth_info",
    "fetch_pre_auth_code",
    "fetch_app_permissions",
    "fetch_corp_token",
    "fetch_corp_access_token",
    "fetch_agent_detail",
    "fetch_agent_list",
    "WebOAuthApi",
    "get_web_oauth_api",
    "build_oauth2_url",
    "EnterpriseContactApi",
    "get_enterprise_contact_api",
    "CorpClient",
]
