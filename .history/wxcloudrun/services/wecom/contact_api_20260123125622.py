"""通讯录相关 API。

封装企业微信通讯录接口，提供查询用户与部门信息的简洁方法。
"""
from typing import Any, Dict
from .base import BaseClient


class ContactApi(BaseClient):
    def get_user(self, corp_access_token: str, userid: str) -> Dict[str, Any]:
        """查询指定用户的详情。

        参数：企业 access_token 与用户 userid。
        返回值为企业微信用户信息 JSON。"""
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/get"
        data = self._do_get(url, params={"access_token": corp_access_token, "userid": userid})
        self._raise_if_errcode(data, "get_user")
        return data

    def get_department(self, corp_access_token: str, dept_id: int) -> Dict[str, Any]:
        """获取指定部门的信息。

        参数：企业 access_token 与部门 id，返回部门结构化信息。
        """
        url = "https://qyapi.weixin.qq.com/cgi-bin/department/get"
        data = self._do_get(url, params={"access_token": corp_access_token, "id": dept_id})
        self._raise_if_errcode(data, "get_department")
        return data
