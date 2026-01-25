"""企业微信客服 - 接待人员管理接口占位。

用于绑定/解绑接待人员、查询接待人员列表等。
"""
from typing import Any, Dict
from ..base import BaseClient, WeComApiError


class KfStaffApi(BaseClient):
    """接待人员相关接口。"""

    def list_staffs(self, access_token: str, open_kfid: str) -> Dict[str, Any]:
        """查询某客服账号下的接待人员列表（待实现）。"""
        raise NotImplementedError

    def add_staffs(self, access_token: str, open_kfid: str, user_ids: list[str]) -> Dict[str, Any]:
        """为客服账号添加接待人员（待实现）。"""
        raise NotImplementedError

    def del_staffs(self, access_token: str, open_kfid: str, user_ids: list[str]) -> Dict[str, Any]:
        """从客服账号移除接待人员（待实现）。"""
        raise NotImplementedError
