"""联系我 / 客户入群方式管理（客户联系）。"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
from ..base import BaseClient, WeComApiError
from wxcloudrun.dao import upsert_corp_config, upsert_group_chat, query_group_chat


class ContactWayApi(BaseClient):
    """封装 externalcontact 联系我、入群方式相关接口。"""

    def add_contact_way(self, access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """配置「联系我」二维码/小程序按钮。payload 需按官方格式。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        if not isinstance(payload, dict):
            raise WeComApiError("payload must be dict")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/add_contact_way"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.add_contact_way", required_keys=["config_id"])
        return data

    def get_contact_way(self, access_token: str, config_id: str) -> Dict[str, Any]:
        """获取已配置的「联系我」方式详情。"""
        if not access_token or not config_id:
            raise WeComApiError("missing access_token or config_id")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/get_contact_way"
        payload = {"config_id": config_id}
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.get_contact_way", required_keys=["contact_way"])
        return data

    def list_contact_way(
        self,
        access_token: str,
        *,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """获取企业已配置的「联系我」列表（不含临时会话）。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        payload: Dict[str, Any] = {}
        if start_time:
            payload["start_time"] = start_time
        if end_time:
            payload["end_time"] = end_time
        if cursor:
            payload["cursor"] = cursor
        if limit:
            payload["limit"] = limit
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/list_contact_way"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.list_contact_way", required_keys=["contact_way"])
        return data

    def update_contact_way(self, access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """更新已配置的「联系我」方式（覆盖更新）。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        if not isinstance(payload, dict) or not payload.get("config_id"):
            raise WeComApiError("payload with config_id is required")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/update_contact_way"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.update_contact_way")
        return data

    def delete_contact_way(self, access_token: str, config_id: str) -> Dict[str, Any]:
        """删除已配置的「联系我」方式。"""
        if not access_token or not config_id:
            raise WeComApiError("missing access_token or config_id")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/del_contact_way"
        payload = {"config_id": config_id}
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.del_contact_way")
        return data

    def close_temp_chat(self, access_token: str, userid: str, external_userid: str) -> Dict[str, Any]:
        """结束临时会话，发送结束语。"""
        if not access_token or not userid or not external_userid:
            raise WeComApiError("missing access_token/userid/external_userid")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/close_temp_chat"
        payload = {"userid": userid, "external_userid": external_userid}
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.close_temp_chat")
        return data

    # 进群方式配置
    def add_join_way(self, access_token: str, payload: Dict[str, Any], *, corp_id: Optional[str] = None) -> Dict[str, Any]:
        """配置客户群「加入群聊」二维码/小程序按钮。payload 需按官方格式。

        若传入 corp_id，则会把 join_way 写入 corp_config_id，并同步 group_chats（如有）。
        返回值包含 config_id；若成功获取 join_way，会附带 join_way。
        """
        if not access_token:
            raise WeComApiError("missing access_token")
        if not isinstance(payload, dict):
            raise WeComApiError("payload must be dict")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/groupchat/add_join_way"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.groupchat.add_join_way", required_keys=["config_id"])
        config_id = data.get("config_id")
        join_way = None
        if config_id:
            try:
                join_resp = self.get_join_way(access_token, config_id)
                join_way = join_resp.get("join_way") if isinstance(join_resp, dict) else None
            except Exception:
                join_way = None

        if corp_id and join_way:
            self._store_join_way(corp_id, join_way)

        if join_way:
            data["join_way"] = join_way
        return data

    def _store_join_way(self, corp_id: str, join_way: Dict[str, Any]) -> None:
        """将 join_way 记录写入 corp_config_id，并同步 group_chats。"""
        config_id = join_way.get("config_id")
        chat_ids = join_way.get("chat_id_list") or []
        if not isinstance(chat_ids, list):
            chat_ids = []
        now = datetime.now(timezone.utc)

        if chat_ids:
            for chat_id in chat_ids:
                upsert_corp_config(
                    {
                        "corp_id": corp_id,
                        "chat_id": chat_id,
                        "config_id": config_id,
                        "join_way": join_way,
                        "contact_way": None,
                        "updated_at": now,
                        "created_at": now,
                    }
                )

                existing = query_group_chat(chat_id)
                if existing:
                    existing["join_way"] = join_way
                    existing["join_way_config_id"] = config_id
                    existing["updated_at"] = now
                    upsert_group_chat(existing)
        else:
            upsert_corp_config(
                {
                    "corp_id": corp_id,
                    "chat_id": None,
                    "config_id": config_id,
                    "join_way": join_way,
                    "contact_way": None,
                    "updated_at": now,
                    "created_at": now,
                }
            )

    def get_join_way(self, access_token: str, config_id: str) -> Dict[str, Any]:
        if not access_token or not config_id:
            raise WeComApiError("missing access_token or config_id")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/groupchat/get_join_way"
        payload = {"config_id": config_id}
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.groupchat.get_join_way", required_keys=["join_way"])
        return data

    def update_join_way(self, access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not access_token:
            raise WeComApiError("missing access_token")
        if not isinstance(payload, dict) or not payload.get("config_id"):
            raise WeComApiError("payload with config_id is required")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/groupchat/update_join_way"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.groupchat.update_join_way")
        return data

    def delete_join_way(self, access_token: str, config_id: str) -> Dict[str, Any]:
        if not access_token or not config_id:
            raise WeComApiError("missing access_token or config_id")
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/groupchat/del_join_way"
        payload = {"config_id": config_id}
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.groupchat.del_join_way")
        return data
