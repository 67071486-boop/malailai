"""应用授权相关接口（自建应用：无 suite / 永久授权码流程）。"""
from typing import Any, Dict

from ..base import BaseClient, WeComApiError
from ..agent.agent_api import AgentApi
from wecom.services.service import token_service
import config


class AppAuthApi(BaseClient):
    def __init__(self, session=None, timeout: int = 10):
        super().__init__(session=session, timeout=timeout)
        self._timeout = timeout
        self._agent_api = AgentApi(session=self.session, timeout=timeout)

    def get_pre_auth_code(self, suite_id: str) -> Dict[str, Any]:
        del suite_id
        raise WeComApiError("自建应用不支持 get_pre_auth_code（仅第三方应用安装授权使用）")

    def get_permanent_code(self, auth_code: str) -> Dict[str, Any]:
        del auth_code
        raise WeComApiError("自建应用不支持 get_permanent_code")

    def get_auth_info(self, auth_corpid: str, permanent_code: str) -> Dict[str, Any]:
        """返回结构兼容旧代码：含 auth_corp_info 键（此处为 agent/get 详情）。"""
        del permanent_code
        cid = auth_corpid or config.WXWORK_CORP_ID
        token = token_service.get_corp_access_token(cid)
        if not token:
            raise WeComApiError("missing access_token")
        if not getattr(config, "WXWORK_AGENT_ID", None):
            raise WeComApiError("missing WXWORK_AGENT_ID")
        detail = self._agent_api.get_agent(token, config.WXWORK_AGENT_ID)
        return {"auth_corp_info": detail}

    def get_corp_token(self, auth_corpid: str, permanent_code: str) -> Dict[str, Any]:
        del permanent_code
        cid = auth_corpid or config.WXWORK_CORP_ID
        token = token_service.get_corp_access_token(cid)
        if not token:
            raise WeComApiError("missing access_token")
        return {"access_token": token, "expires_in": 7200}

    def get_app_permissions(self, access_token: str) -> Dict[str, Any]:
        if not access_token:
            raise WeComApiError("missing access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/agent/get_permissions"
        data = self._do_post(url + f"?access_token={access_token}", json={})
        self._raise_if_errcode(data, "get_app_permissions", required_keys=["app_permissions"])
        return data


def fetch_pre_auth_code(
    suite_id: str,
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    client = AppAuthApi(session=session, timeout=timeout)
    return client.get_pre_auth_code(suite_id)


def fetch_auth_info(
    auth_corpid: str,
    permanent_code: str,
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    client = AppAuthApi(session=session, timeout=timeout)
    return client.get_auth_info(auth_corpid, permanent_code)


def fetch_corp_token(
    auth_corpid: str,
    permanent_code: str,
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    client = AppAuthApi(session=session, timeout=timeout)
    return client.get_corp_token(auth_corpid, permanent_code)


def fetch_app_permissions(
    access_token: str,
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    client = AppAuthApi(session=session, timeout=timeout)
    return client.get_app_permissions(access_token)
