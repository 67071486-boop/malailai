"""客户标签管理（客户联系）。"""
from typing import Any, Dict, List, Optional
from ..base import BaseClient, WeComApiError


class ContactTagApi(BaseClient):
    """封装企业客户标签的获取/新增/编辑/删除。"""

    def get_corp_tag_list(
        self,
        access_token: str,
        *,
        tag_ids: Optional[List[str]] = None,
        group_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not access_token:
            raise WeComApiError("missing access_token")
        payload: Dict[str, Any] = {}
        if tag_ids:
            payload["tag_id"] = tag_ids
        if group_ids:
            payload["group_id"] = group_ids
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/get_corp_tag_list"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.get_corp_tag_list", required_keys=["tag_group"])
        return data

    def add_corp_tag(self, access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not access_token:
            raise WeComApiError("missing access_token")
        if not isinstance(payload, dict):
            raise WeComApiError("payload must be dict")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/add_corp_tag"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.add_corp_tag", required_keys=["tag_group"])
        return data

    def edit_corp_tag(self, access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not access_token:
            raise WeComApiError("missing access_token")
        if not isinstance(payload, dict) or not payload.get("id"):
            raise WeComApiError("payload with id is required")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/edit_corp_tag"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.edit_corp_tag")
        return data

    def delete_corp_tag(
        self,
        access_token: str,
        *,
        tag_ids: Optional[List[str]] = None,
        group_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not access_token:
            raise WeComApiError("missing access_token")
        if not tag_ids and not group_ids:
            raise WeComApiError("tag_ids or group_ids required")
        payload: Dict[str, Any] = {}
        if tag_ids:
            payload["tag_id"] = tag_ids
        if group_ids:
            payload["group_id"] = group_ids
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/del_corp_tag"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.del_corp_tag")
        return data
