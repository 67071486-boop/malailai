"""消息发送相关 API。

封装企业微信对外消息发送接口，使用企业 access_token 调用。
"""
from typing import Any, Dict
from .base import BaseClient


class MessageApi(BaseClient):
    def send_message(self, corp_access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """发送企业消息。

        `payload` 应为企业微信 message/send 接口需要的 JSON 结构，
        本方法负责发起请求并校验返回结果。
        """
        url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
        data = self._do_post(url + f"?access_token={corp_access_token}", json=payload)
        self._raise_if_errcode(data, "send_message")
        return data
