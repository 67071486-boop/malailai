"""通讯录管理模块：封装企业微信通讯录（用户/部门）基础 CRUD 接口。

提供类 `ContactManager`，包含：
- 用户：get/create/update/delete/simplelist
- 部门：list/create/update/delete

所有方法均返回解析后的 JSON（dict），遇到网络或 API 错误会抛出 `WeComApiError`。
"""
from typing import Any, Dict, Optional
from .base import BaseClient, WeComApiError


class ContactManager(BaseClient):
    """企业通讯录管理客户端。

    该客户端方法都要求传入企业 `access_token`（即企业 access_token 或代开发应用 token），
    也可通过子类或外部注入方式改造为自动从缓存获取 token。
    """

    def get_user(self, access_token: str, userid: str) -> Dict[str, Any]:
        """获取用户详情。

        GET https://qyapi.weixin.qq.com/cgi-bin/user/get?access_token=ACCESS_TOKEN&userid=USERID
        返回用户完整信息 JSON。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/get"
        data = self._do_get(url, params={"access_token": access_token, "userid": userid})
        self._raise_if_errcode(data, "get_user")
        return data

    def create_user(self, access_token: str, userinfo: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户。

        POST https://qyapi.weixin.qq.com/cgi-bin/user/create?access_token=ACCESS_TOKEN
        请求体格式请参考企业微信 API 文档（包含 userid、name、department 等字段）。
        """
        if not access_token:
            raise WeComApiError("missing access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/create"
        data = self._do_post(url + f"?access_token={access_token}", json=userinfo)
        self._raise_if_errcode(data, "create_user")
        return data

    def update_user(self, access_token: str, userinfo: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户信息（按企业微信 user/update 接口）。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/update"
        data = self._do_post(url + f"?access_token={access_token}", json=userinfo)
        self._raise_if_errcode(data, "update_user")
        return data

    def delete_user(self, access_token: str, userid: str) -> Dict[str, Any]:
        """删除用户。

        GET https://qyapi.weixin.qq.com/cgi-bin/user/delete?access_token=ACCESS_TOKEN&userid=USERID
        """
        if not access_token:
            raise WeComApiError("missing access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/delete"
        data = self._do_get(url, params={"access_token": access_token, "userid": userid})
        self._raise_if_errcode(data, "delete_user")
        return data

    def simplelist(self, access_token: str, department_id: int, fetch_child: int = 0) -> Dict[str, Any]:
        """按部门获取成员（简要信息），对大多场景足够使用。

        GET https://qyapi.weixin.qq.com/cgi-bin/user/simplelist?access_token=ACCESS_TOKEN&department_id=ID&fetch_child=0
        """
        if not access_token:
            raise WeComApiError("missing access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/simplelist"
        params = {"access_token": access_token, "department_id": department_id, "fetch_child": fetch_child}
        data = self._do_get(url, params=params)
        self._raise_if_errcode(data, "simplelist")
        return data

    # 部门相关
    def list_departments(self, access_token: str, id: Optional[int] = None) -> Dict[str, Any]:
        """获取部门列表；可指定 id 查询子部门/本部门信息。

        GET https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token=ACCESS_TOKEN&id=ID
        """
        if not access_token:
            raise WeComApiError("missing access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/department/list"
        params = {"access_token": access_token}
        if id is not None:
            params["id"] = id
        data = self._do_get(url, params=params)
        self._raise_if_errcode(data, "list_departments")
        return data

    def create_department(self, access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """创建部门，payload 需包含 name、parentid 等字段。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/department/create"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "create_department")
        return data

    def update_department(self, access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """更新部门信息（id 必须在 payload 中）。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/department/update"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "update_department")
        return data

    def delete_department(self, access_token: str, id: int) -> Dict[str, Any]:
        """删除部门。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/department/delete"
        data = self._do_get(url, params={"access_token": access_token, "id": id})
        self._raise_if_errcode(data, "delete_department")
        return data


# 便捷工厂
def get_contact_manager(session: Optional[Any] = None) -> ContactManager:
    return ContactManager(session=session)
