"""消息推送（客户联系）占位实现。"""
from ..base import BaseClient


class ContactMessagePushApi(BaseClient):
    """负责客户联系消息/任务推送相关接口（占位）。"""

    def placeholder(self):
        raise NotImplementedError("ContactMessagePushApi methods to be implemented")
