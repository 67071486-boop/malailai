"""企业微信客服 - 统计管理接口占位。

后续可封装会话统计、消息统计等接口。
"""
from typing import Any, Dict
from ..base import BaseClient, WeComApiError


class KfStatsApi(BaseClient):
    """统计类接口。"""

    def get_servicer_stat(self, access_token: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取接待人员统计数据（待实现）。"""
        raise NotImplementedError

    def get_session_stat(self, access_token: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取会话/消息统计数据（待实现）。"""
        raise NotImplementedError
