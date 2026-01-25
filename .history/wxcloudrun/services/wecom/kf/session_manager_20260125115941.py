"""企业微信客服 - 会话状态与事件响应接口封装。

包含：获取/变更会话状态，发送事件响应消息（欢迎语/提示语等）。
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
