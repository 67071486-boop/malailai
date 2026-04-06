"""企业微信客服 - 接待人员管理接口封装。

包含添加/删除接待人员、查询接待人员列表。
"""
from typing import Any, Dict, List, Optional
from ..base import BaseClient, WeComApiError


class KfStaffApi(BaseClient):
    """接待人员相关接口。"""

    def list_staffs(self, access_token: str, open_kfid: str) -> Dict[str, Any]:
        """查询某客服账号下的接待人员列表。"""
        if not access_token or not open_kfid:
            raise WeComApiError("missing access_token or open_kfid")
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/servicer/list"
        data = self._do_get(url, params={"access_token": access_token, "open_kfid": open_kfid})
        self._raise_if_errcode(data, "kf.servicer.list", required_keys=["servicer_list"])
        return data

    def add_staffs(
        self,
        access_token: str,
        open_kfid: str,
        *,
        user_ids: Optional[List[str]] = None,
        department_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """为客服账号添加接待人员/部门，userid_list 或 department_id_list 至少一个。"""
        if not access_token or not open_kfid:
            raise WeComApiError("missing access_token or open_kfid")
        if not user_ids and not department_ids:
            raise WeComApiError("user_ids or department_ids required")
        payload: Dict[str, Any] = {"open_kfid": open_kfid}
        if user_ids:
            payload["userid_list"] = user_ids
        if department_ids:
            payload["department_id_list"] = department_ids
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/servicer/add"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "kf.servicer.add", required_keys=["result_list"])
        return data

    def del_staffs(
        self,
        access_token: str,
        open_kfid: str,
        *,
        user_ids: Optional[List[str]] = None,
        department_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """从客服账号移除接待人员/部门，userid_list 或 department_id_list 至少一个。"""
        if not access_token or not open_kfid:
            raise WeComApiError("missing access_token or open_kfid")
        if not user_ids and not department_ids:
            raise WeComApiError("user_ids or department_ids required")
        payload: Dict[str, Any] = {"open_kfid": open_kfid}
        if user_ids:
            payload["userid_list"] = user_ids
        if department_ids:
            payload["department_id_list"] = department_ids
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/servicer/del"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "kf.servicer.del", required_keys=["result_list"])
        return data
