"""应用管理 API。"""
from typing import Any, Dict, Union
from ..base import BaseClient


class AgentApi(BaseClient):
    def get_agent(self, access_token: str, agent_id: Union[str, int]) -> Dict[str, Any]:
        """获取指定应用详情。"""
        url = "https://qyapi.weixin.qq.com/cgi-bin/agent/get"
        params = {"access_token": access_token, "agentid": agent_id}
        data = self._do_get(url, params=params)
        self._raise_if_errcode(data, "agent_get")
        return data

    def list_agents(self, access_token: str) -> Dict[str, Any]:
        """获取当前凭证可访问的应用列表。"""
        url = "https://qyapi.weixin.qq.com/cgi-bin/agent/list"
        data = self._do_get(url, params={"access_token": access_token})
        self._raise_if_errcode(data, "agent_list")
        return data


def fetch_agent_detail(access_token: str, agent_id: Union[str, int]) -> Dict[str, Any]:
    return AgentApi().get_agent(access_token, agent_id)


def fetch_agent_list(access_token: str) -> Dict[str, Any]:
    return AgentApi().list_agents(access_token)
