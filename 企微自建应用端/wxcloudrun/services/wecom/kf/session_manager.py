"""企业微信客服 - 会话状态、事件响应与消息收发接口封装。

包含：获取/变更会话状态、事件响应消息、拉取历史消息、发送消息。
"""
from typing import Any, Dict, Optional
from ..base import BaseClient, WeComApiError


class KfSessionApi(BaseClient):
    """会话分配与事件响应相关接口。"""

    def get_service_state(self, access_token: str, open_kfid: str, external_userid: str) -> Dict[str, Any]:
        """获取会话状态。"""
        if not access_token or not open_kfid or not external_userid:
            raise WeComApiError("missing access_token/open_kfid/external_userid")
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/service_state/get"
        payload = {"open_kfid": open_kfid, "external_userid": external_userid}
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "kf.service_state.get", required_keys=["service_state"])
        return data

    def trans_service_state(
        self,
        access_token: str,
        open_kfid: str,
        external_userid: str,
        service_state: int,
        *,
        servicer_userid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """变更会话状态。需要时可传 servicer_userid（例如 state=3）。"""
        if not access_token or not open_kfid or not external_userid:
            raise WeComApiError("missing access_token/open_kfid/external_userid")
        payload: Dict[str, Any] = {
            "open_kfid": open_kfid,
            "external_userid": external_userid,
            "service_state": service_state,
        }
        if servicer_userid:
            payload["servicer_userid"] = servicer_userid
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/service_state/trans"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "kf.service_state.trans")
        return data

    def send_msg_on_event(self, access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """发送事件响应消息（欢迎语/结束语/排队提示等）。

        `payload` 需包含 code、msgtype 等字段，遵循官方消息格式。
        """
        if not access_token:
            raise WeComApiError("missing access_token")
        if not payload or "code" not in payload:
            raise WeComApiError("payload with code is required")
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg_on_event"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "kf.send_msg_on_event", required_keys=["msgid"])
        return data

    def sync_msg(
        self,
        access_token: str,
        open_kfid: str,
        *,
        cursor: Optional[str] = None,
        token: Optional[str] = None,
        limit: int = 1000,
        voice_format: int = 0,
    ) -> Dict[str, Any]:
        """拉取最近3天的消息/事件。

        - open_kfid 必填；cursor 可用于增量拉取；token 为回调返回的 token，10 分钟有效。
        - limit 默认/上限 1000。
        """
        if not access_token or not open_kfid:
            raise WeComApiError("missing access_token or open_kfid")
        if limit < 1 or limit > 1000:
            raise WeComApiError("limit must be 1~1000")
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/sync_msg"
        payload: Dict[str, Any] = {
            "open_kfid": open_kfid,
            "limit": limit,
            "voice_format": voice_format,
        }
        if cursor:
            payload["cursor"] = cursor
        if token:
            payload["token"] = token
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "kf.sync_msg", required_keys=["msg_list", "has_more"])
        return data

    def send_message(self, access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """发送客服消息（文本/图片/语音/视频/文件/图文/小程序/菜单/位置等）。

        `payload` 需包含 touser、open_kfid、msgtype 等字段，遵循官方消息格式；
        msgid 可选但需在同一客服账号下唯一。
        """
        if not access_token:
            raise WeComApiError("missing access_token")
        if not payload or "touser" not in payload or "open_kfid" not in payload or "msgtype" not in payload:
            raise WeComApiError("payload must include touser, open_kfid, msgtype")
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "kf.send_msg", required_keys=["msgid"])
        return data
