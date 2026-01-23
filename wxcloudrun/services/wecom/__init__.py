"""WeCom API 按业务域拆分后的工厂与兼容入口。"""
import requests
from typing import Optional
from .base import BaseClient, WeComApiError
from .suite_api import SuiteApi, fetch_suite_access_token
from .corp_auth_api import CorpAuthApi, fetch_corp_access_token
from .contact_api import ContactApi
from .message_api import MessageApi
from .token_provider import SuiteTokenProvider, CorpTokenProvider

_shared_session = requests.Session()
_suite_token_provider = SuiteTokenProvider()
_corp_token_provider = CorpTokenProvider()


def get_suite_api(session: Optional[requests.Session] = None) -> SuiteApi:
    return SuiteApi(session=session or _shared_session, token_provider=_suite_token_provider)


def get_corp_auth_api(session: Optional[requests.Session] = None) -> CorpAuthApi:
    return CorpAuthApi(
        session=session or _shared_session,
        suite_token_provider=_suite_token_provider,
        corp_token_provider=_corp_token_provider,
    )


def get_contact_api(session: Optional[requests.Session] = None) -> ContactApi:
    return ContactApi(session=session or _shared_session)


def get_message_api(session: Optional[requests.Session] = None) -> MessageApi:
    return MessageApi(session=session or _shared_session)


class CorpClient:
    """兼容旧接口的组合客户端。"""

    def __init__(self, session: Optional[requests.Session] = None):
        self._auth_api = get_corp_auth_api(session)
        self._contact_api = get_contact_api(session)
        self._message_api = get_message_api(session)

    def get_corp_access_token(self, suite_id: str, corp_id: str, permanent_code: str):
        return self._auth_api.get_corp_token(suite_id, corp_id, permanent_code)

    def send_message(self, corp_access_token: str, payload: dict):
        return self._message_api.send_message(corp_access_token, payload)

    def get_user(self, corp_access_token: str, userid: str):
        return self._contact_api.get_user(corp_access_token, userid)

    def get_department(self, corp_access_token: str, dept_id: int):
        return self._contact_api.get_department(corp_access_token, dept_id)


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
    "ContactApi",
    "MessageApi",
    "SuiteClient",
    "get_suite_client",
    "get_corp_client",
    "get_suite_api",
    "get_corp_auth_api",
    "get_contact_api",
    "get_message_api",
    "fetch_suite_access_token",
    "fetch_corp_access_token",
    "CorpClient",
]
