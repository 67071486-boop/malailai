"""客户管理（客户联系）：客户列表、详情、备注。"""
from typing import Any, Dict, Optional
from ..base import BaseClient, WeComApiError


class ContactCustomerApi(BaseClient):
    """封装 externalcontact 客户相关接口。"""

    def list_customers(self, access_token: str, userid: str) -> Dict[str, Any]:
        """获取指定成员的客户 external_userid 列表。"""
        if not access_token or not userid:
            raise WeComApiError("missing access_token or userid")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/list"
        params = {"access_token": access_token, "userid": userid}
        data = self._do_get(url, params=params)
        self._raise_if_errcode(data, "externalcontact.list", required_keys=["external_userid"])
        return data

    def get_customer(self, access_token: str, external_userid: str, *, cursor: Optional[str] = None) -> Dict[str, Any]:
        """获取客户详情；当跟进人>500 需用 cursor 分页。"""
        if not access_token or not external_userid:
            raise WeComApiError("missing access_token or external_userid")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/get"
        params = {"access_token": access_token, "external_userid": external_userid}
        if cursor:
            params["cursor"] = cursor
        data = self._do_get(url, params=params)
        self._raise_if_errcode(data, "externalcontact.get", required_keys=["external_contact"])
        return data

    def remark_customer(self, access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """修改指定成员对客户的备注信息。payload 需含 userid/external_userid。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        if not isinstance(payload, dict) or not payload.get("userid") or not payload.get("external_userid"):
            raise WeComApiError("payload must include userid and external_userid")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/remark"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.remark")
        return data
