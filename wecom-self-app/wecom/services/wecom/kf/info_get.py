"""企业微信客服 - 基础信息获取接口封装。

当前实现：批量获取客户基础信息。
"""
from typing import Any, Dict, List
from ..base import BaseClient, WeComApiError


class KfInfoApi(BaseClient):
    """其他基础信息查询接口。"""

    def batch_get_customer(
        self,
        access_token: str,
        external_userid_list: List[str],
        *,
        need_enter_session_context: int = 0,
    ) -> Dict[str, Any]:
        """批量获取客户基础信息（1~100 external_userid）。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        if not external_userid_list or not isinstance(external_userid_list, list):
            raise WeComApiError("external_userid_list is required and must be a list")
        if len(external_userid_list) < 1 or len(external_userid_list) > 100:
            raise WeComApiError("external_userid_list size must be 1~100")
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/customer/batchget"
        payload = {
            "external_userid_list": external_userid_list,
            "need_enter_session_context": int(need_enter_session_context),
        }
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "kf.customer.batchget", required_keys=["customer_list"])
        return data
