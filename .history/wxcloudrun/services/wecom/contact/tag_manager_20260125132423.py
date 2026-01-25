"""客户标签管理（客户联系）占位实现。"""
from ..base import BaseClient


class ContactTagApi(BaseClient):
    """负责外部联系人标签的增删改查、分组等（占位）。"""

    def placeholder(self):
        raise NotImplementedError("ContactTagApi methods to be implemented")
