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


class MessageReceiver:
    """占位：接收与解析企业微信推送的消息/事件。

    后续可实现：XML 解密（WXBizMsgCrypt）、xmltodict 解析、InfoType 分发等。
    """

    def __init__(self, session: Any = None):
        self.session = session

    def parse_message(self, xml_text: str) -> Dict[str, Any]:
        """占位方法：解析/解密收到的 XML 文本并返回 dict。

        当前实现为占位，调用方可在此处补充解密与解析逻辑。
        """
        # TODO: 实现解密与 xml->dict 转换
        return {"raw_xml": xml_text}


__all__ = ["MessageApi", "MessageReceiver"]
