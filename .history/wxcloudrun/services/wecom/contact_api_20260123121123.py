"""通讯录相关 API。"""
from typing import Any, Dict
from .base import BaseClient


class ContactApi(BaseClient):
    def get_user(self, corp_access_token: str, userid: str) -> Dict[str, Any]:
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/get"
        data = self._do_get(url, params={"access_token": corp_access_token, "userid": userid})
        self._raise_if_errcode(data, "get_user")
        return data

    def get_department(self, corp_access_token: str, dept_id: int) -> Dict[str, Any]:
        url = "https://qyapi.weixin.qq.com/cgi-bin/department/get"
        data = self._do_get(url, params={"access_token": corp_access_token, "id": dept_id})
        self._raise_if_errcode(data, "get_department")
        return data
