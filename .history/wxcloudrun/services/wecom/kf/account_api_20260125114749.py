"""企业微信客服 - 账号与管理相关接口占位。

参考现有 BaseClient 用法：继承 BaseClient，使用 `_do_get/_do_post`，并通过 `_raise_if_errcode` 做统一错误处理。
后续根据官方文档填充实际 URL 和参数。
"""
from typing import Any, Dict, Optional
from ..base import BaseClient, WeComApiError


class KfAccountApi(BaseClient):
    """客服账号的增删改查等管理接口。"""

    def list_accounts(self, access_token: str) -> Dict[str, Any]:
        """列出客服账号列表（待实现）。"""
        raise NotImplementedError

    def create_account(self, access_token: str, name: str, media_id: Optional[str] = None) -> Dict[str, Any]:
        """创建客服账号（待实现）。"""
        raise NotImplementedError

    def update_account(self, access_token: str, open_kfid: str, name: Optional[str] = None, media_id: Optional[str] = None) -> Dict[str, Any]:
        """更新客服账号信息（待实现）。"""
        raise NotImplementedError

    def delete_account(self, access_token: str, open_kfid: str) -> Dict[str, Any]:
        """删除客服账号（待实现）。"""
        raise NotImplementedError

    def get_account(self, access_token: str, open_kfid: str) -> Dict[str, Any]:
        """获取单个客服账号详情（待实现）。"""
        raise NotImplementedError
