"""企业微信客服 - 基础信息获取接口占位。

用于获取客服帐号基本信息、客户信息等辅助数据。
"""
from typing import Any, Dict
from ..base import BaseClient, WeComApiError


class KfInfoApi(BaseClient):
    """其他基础信息查询接口。"""

    def get_servicer_state(self, access_token: str, open_kfid: str, servicer_userid: str) -> Dict[str, Any]:
        """查询接待人员状态（待实现）。"""
        raise NotImplementedError

    def get_customer_info(self, access_token: str, external_userid: str) -> Dict[str, Any]:
        """获取客户信息（待实现）。"""
        raise NotImplementedError
