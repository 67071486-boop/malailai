"""企业微信客服 - 账号与管理接口封装。

包含：添加/删除/更新客服账号、分页列表、获取客服链接。
"""
from typing import Any, Dict, Optional
from ..base import BaseClient, WeComApiError


class KfAccountApi(BaseClient):
    """客服账号的增删改查等管理接口。"""

    def add_account(self, access_token: str, name: str, media_id: str) -> Dict[str, Any]:
        """添加客服账号，返回 `open_kfid`。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        if not name or not media_id:
            raise WeComApiError("name and media_id are required")
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/account/add"
        data = self._do_post(url + f"?access_token={access_token}", json={"name": name, "media_id": media_id})
        self._raise_if_errcode(data, "kf.account.add", required_keys=["open_kfid"])
        return data

    def delete_account(self, access_token: str, open_kfid: str) -> Dict[str, Any]:
        """删除客服账号。"""
        if not access_token or not open_kfid:
            raise WeComApiError("missing access_token or open_kfid")
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/account/del"
        data = self._do_post(url + f"?access_token={access_token}", json={"open_kfid": open_kfid})
        self._raise_if_errcode(data, "kf.account.del")
        return data

    def update_account(
        self,
        access_token: str,
        open_kfid: str,
        *,
        name: Optional[str] = None,
        media_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """修改客服账号名称/头像，至少提供 name 或 media_id。"""
        if not access_token or not open_kfid:
            raise WeComApiError("missing access_token or open_kfid")
        if not name and not media_id:
            raise WeComApiError("name or media_id required for update")
        payload: Dict[str, Any] = {"open_kfid": open_kfid}
        if name:
            payload["name"] = name
        if media_id:
            payload["media_id"] = media_id
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/account/update"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "kf.account.update")
        return data

    def list_accounts(self, access_token: str, *, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """分页获取客服账号列表（limit 1~100）。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/account/list"
        payload = {"offset": offset, "limit": limit}
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "kf.account.list", required_keys=["account_list"])
        return data

    def get_contact_way(self, access_token: str, open_kfid: str, *, scene: Optional[str] = None) -> Dict[str, Any]:
        """获取客服账号链接，scene 可选。"""
        if not access_token or not open_kfid:
            raise WeComApiError("missing access_token or open_kfid")
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/add_contact_way"
        payload: Dict[str, Any] = {"open_kfid": open_kfid}
        if scene:
            payload["scene"] = scene
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "kf.add_contact_way", required_keys=["url"])
        return data
