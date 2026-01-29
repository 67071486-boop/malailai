"""WeCom API 按业务域拆分后的工厂与兼容入口。

本包提供按业务域组织的 API 客户端工厂（如 `get_suite_api`、`get_corp_auth_api` 等），
以及若干兼容旧代码的薄封装（`CorpClient`、`get_suite_client` 等）。
推荐调用方式为通过对应的 `get_*_api` 获取客户端实例后调用其方法。
"""
import requests
from typing import Optional
from .base import BaseClient, WeComApiError
from .auth.suite_api import SuiteApi, fetch_suite_access_token
from .auth.corp_auth_api import CorpAuthApi, fetch_corp_access_token
from .auth.app_auth_api import AppAuthApi, fetch_pre_auth_code, fetch_auth_info, fetch_app_permissions, fetch_corp_token
from .agent import AgentApi, fetch_agent_detail, fetch_agent_list
from .auth.web_oauth import WebOAuthApi, build_oauth2_url
from .enterpriseContact import EnterpriseContactApi, get_enterprise_contact_api
_shared_session = requests.Session()


def get_suite_api(session: Optional[requests.Session] = None) -> SuiteApi:
    """返回用于调用 Suite 相关接口的 `SuiteApi` 实例。"""
    return SuiteApi(session=session or _shared_session)


def get_corp_auth_api(session: Optional[requests.Session] = None) -> CorpAuthApi:
    """返回用于处理企业授权与 corp_token 的 `CorpAuthApi` 实例。"""
    return CorpAuthApi(session=session or _shared_session)


def get_agent_api(session: Optional[requests.Session] = None) -> AgentApi:
    """返回用于访问应用管理接口的 `AgentApi` 实例。"""
    return AgentApi(session=session or _shared_session)


def get_auth_info_api(session: Optional[requests.Session] = None) -> AppAuthApi:
    """兼容命名：返回 `AppAuthApi`，用于查询企业授权信息等。"""
    return AppAuthApi(session=session or _shared_session)


def get_app_auth_api(session: Optional[requests.Session] = None) -> AppAuthApi:
    return AppAuthApi(session=session or _shared_session)


def get_web_oauth_api(session: Optional[requests.Session] = None) -> WebOAuthApi:
    return WebOAuthApi(session=session or _shared_session)


class CorpClient:
    """兼容旧接口的组合客户端。

    提供组合型的客户端用于快速迁移旧代码，封装了 corp_token、通讯录、消息发送等功能。
    新代码建议直接使用对应的 `*Api` 类以实现更精细的依赖注入与测试。
    """

    def __init__(self, session: Optional[requests.Session] = None):
        self._auth_api = get_corp_auth_api(session)

    def get_corp_access_token(self, suite_id: str, corp_id: str, permanent_code: str):
        return self._auth_api.get_corp_token(suite_id, corp_id, permanent_code)


# 兼容旧工厂函数
SuiteClient = SuiteApi


def get_suite_client() -> SuiteApi:
    return get_suite_api()


def get_corp_client() -> CorpClient:
    return CorpClient()


__all__ = [
    "BaseClient",
    "WeComApiError",
    "SuiteApi",
    "CorpAuthApi",
    "MessageApi",
    "AgentApi",
    "SuiteClient",
    "get_suite_client",
    "get_corp_client",
    "get_suite_api",
    "get_corp_auth_api",
    "get_contact_api",
    "get_agent_api",
    "get_auth_info_api",
    "get_app_auth_api",
    "fetch_suite_access_token",
    "fetch_corp_access_token",
    "fetch_auth_info",
    "fetch_pre_auth_code",
    "fetch_app_permissions",
    "fetch_corp_token",
    "fetch_agent_detail",
    "fetch_agent_list",
    "WebOAuthApi",
    "get_web_oauth_api",
    "build_oauth2_url",
    "EnterpriseContactApi",
    "get_enterprise_contact_api",
    "CorpClient",
]
