"""在职继承（客户联系）占位实现。"""
from ..base import BaseClient


class ContactOnjobTransferApi(BaseClient):
    """负责在职继承规则/执行相关接口（占位）。"""

    def placeholder(self):
        raise NotImplementedError("ContactOnjobTransferApi methods to be implemented")
