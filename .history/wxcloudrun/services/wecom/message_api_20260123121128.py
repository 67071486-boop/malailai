"""消息发送相关 API。"""
from typing import Any, Dict
from .base import BaseClient


class MessageApi(BaseClient):
    def send_message(self, corp_access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
        data = self._do_post(url + f"?access_token={corp_access_token}", json=payload)
        self._raise_if_errcode(data, "send_message")
        return data
