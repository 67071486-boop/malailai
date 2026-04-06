"""附件资源上传（客户联系）占位实现。"""
from ..base import BaseClient


class ContactMediaApi(BaseClient):
    """负责客户联系侧的素材/附件上传等接口（占位）。"""

    def placeholder(self):
        raise NotImplementedError("ContactMediaApi methods to be implemented")
