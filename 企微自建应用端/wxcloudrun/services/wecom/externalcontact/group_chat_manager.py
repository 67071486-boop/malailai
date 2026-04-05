"""客户群管理（客户联系）：获取列表与详情。"""
from typing import Any, Dict, List, Optional
from ..base import BaseClient, WeComApiError


class ContactGroupChatApi(BaseClient):
    """封装 externalcontact/groupchat 相关接口。"""

    def list_group_chats(
        self,
        access_token: str,
        *,
        status_filter: int = 0,
        owner_userids: Optional[List[str]] = None,
        cursor: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """获取客户群列表（cursor 分页，limit 1~1000）。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        if limit < 1 or limit > 1000:
            raise WeComApiError("limit must be 1~1000")
        if owner_userids and len(owner_userids) > 100:
            raise WeComApiError("owner_userids max 100")

        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/groupchat/list"
        payload: Dict[str, Any] = {
            "status_filter": status_filter,
            "limit": limit,
        }
        if owner_userids:
            payload["owner_filter"] = {"userid_list": owner_userids}
        if cursor:
            payload["cursor"] = cursor

        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.groupchat.list", required_keys=["group_chat_list"])
        return data

    def get_group_chat(self, access_token: str, chat_id: str, *, need_name: int = 0) -> Dict[str, Any]:
        """获取客户群详情，need_name=1 时返回成员姓名。"""
        if not access_token or not chat_id:
            raise WeComApiError("missing access_token or chat_id")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/groupchat/get"
        payload = {"chat_id": chat_id, "need_name": need_name}
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.groupchat.get", required_keys=["group_chat"])
        return data
