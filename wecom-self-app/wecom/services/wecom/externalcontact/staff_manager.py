"""企业服务人员管理（客户联系）。"""
from ..base import BaseClient, WeComApiError
from typing import Any, Dict


class ContactStaffApi(BaseClient):
    """封装获取配置了客户联系功能的成员列表等接口。"""

    def get_follow_user_list(self, access_token: str) -> Dict[str, Any]:
        """获取已配置客户联系功能的成员列表。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/get_follow_user_list"
        data = self._do_get(url, params={"access_token": access_token})
        self._raise_if_errcode(data, "externalcontact.get_follow_user_list", required_keys=["follow_user"])
        return data
