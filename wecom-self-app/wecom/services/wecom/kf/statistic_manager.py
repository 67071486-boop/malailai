"""企业微信客服 - 统计管理接口封装。

实现：企业汇总统计、接待人员维度统计。
"""
from typing import Any, Dict, Optional
from ..base import BaseClient, WeComApiError


class KfStatsApi(BaseClient):
    """统计类接口。"""

    def get_corp_statistic(
        self,
        access_token: str,
        open_kfid: str,
        start_time: int,
        end_time: int,
    ) -> Dict[str, Any]:
        """获取企业层面客服数据统计（咨询会话数、客户数等）。"""
        if not access_token or not open_kfid:
            raise WeComApiError("missing access_token or open_kfid")
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/get_corp_statistic"
        payload = {
            "open_kfid": open_kfid,
            "start_time": start_time,
            "end_time": end_time,
        }
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "kf.get_corp_statistic", required_keys=["statistic_list"])
        return data

    def get_servicer_statistic(
        self,
        access_token: str,
        open_kfid: str,
        start_time: int,
        end_time: int,
        *,
        servicer_userid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取接待人员统计；不传 servicer_userid 返回账号维度汇总。"""
        if not access_token or not open_kfid:
            raise WeComApiError("missing access_token or open_kfid")
        url = "https://qyapi.weixin.qq.com/cgi-bin/kf/get_servicer_statistic"
        payload: Dict[str, Any] = {
            "open_kfid": open_kfid,
            "start_time": start_time,
            "end_time": end_time,
        }
        if servicer_userid:
            payload["servicer_userid"] = servicer_userid
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "kf.get_servicer_statistic", required_keys=["statistic_list"])
        return data
