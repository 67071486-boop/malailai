"""企业微信客服 - 会话分配与消息发送接口占位。

包含分配会话、发送消息、结束会话等接口。
"""
from typing import Any, Dict
from ..base import BaseClient, WeComApiError


class KfSessionApi(BaseClient):
    """会话分配与消息发送相关接口。"""

    def dispatch(self, access_token: str, open_kfid: str, external_userid: str, servicer_userid: str) -> Dict[str, Any]:
        """分配会话给指定接待人员（待实现）。"""
        raise NotImplementedError

    def send_message(self, access_token: str, msg: Dict[str, Any]) -> Dict[str, Any]:
        """发送客服消息（待实现）。"""
        raise NotImplementedError

    def close_session(self, access_token: str, open_kfid: str, external_userid: str) -> Dict[str, Any]:
        """结束/关闭会话（待实现）。"""
        raise NotImplementedError
