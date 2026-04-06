"""统计管理（客户联系）：成员行为与客户群统计。"""
from typing import Any, Dict, List, Optional
from ..base import BaseClient, WeComApiError


class ContactStatisticApi(BaseClient):
    """封装 externalcontact 统计相关接口。"""

    def get_user_behavior_data(
        self,
        access_token: str,
        *,
        userid_list: Optional[List[str]] = None,
        partyid_list: Optional[List[int]] = None,
        start_time: int,
        end_time: int,
    ) -> Dict[str, Any]:
        """获取成员联系客户数据，时间范围最大30天。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        if start_time is None or end_time is None:
            raise WeComApiError("start_time and end_time are required")
        if not userid_list and not partyid_list:
            raise WeComApiError("userid_list or partyid_list required")
        payload: Dict[str, Any] = {"start_time": start_time, "end_time": end_time}
        if userid_list:
            payload["userid"] = userid_list
        if partyid_list:
            payload["partyid"] = partyid_list
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/get_user_behavior_data"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.get_user_behavior_data", required_keys=["behavior_data"])
        return data

    def groupchat_statistic(
        self,
        access_token: str,
        *,
        day_begin_time: int,
        day_end_time: Optional[int] = None,
        owner_userids: Optional[List[str]] = None,
        order_by: Optional[int] = None,
        order_asc: Optional[int] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """按群主聚合的客户群统计。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        if day_begin_time is None:
            raise WeComApiError("day_begin_time is required")
        payload: Dict[str, Any] = {"day_begin_time": day_begin_time}
        if day_end_time is not None:
            payload["day_end_time"] = day_end_time
        if owner_userids:
            payload["owner_filter"] = {"userid_list": owner_userids}
        if order_by is not None:
            payload["order_by"] = order_by
        if order_asc is not None:
            payload["order_asc"] = order_asc
        if offset is not None:
            payload["offset"] = offset
        if limit is not None:
            payload["limit"] = limit
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/groupchat/statistic"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.groupchat.statistic", required_keys=["items"])
        return data

    def groupchat_statistic_by_day(
        self,
        access_token: str,
        *,
        day_begin_time: int,
        day_end_time: Optional[int] = None,
        owner_userids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """按自然日聚合的客户群统计。"""
        if not access_token:
            raise WeComApiError("missing access_token")
        if day_begin_time is None:
            raise WeComApiError("day_begin_time is required")
        payload: Dict[str, Any] = {"day_begin_time": day_begin_time}
        if day_end_time is not None:
            payload["day_end_time"] = day_end_time
        if owner_userids:
            payload["owner_filter"] = {"userid_list": owner_userids}
        url = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/groupchat/statistic_group_by_day"
        data = self._do_post(url + f"?access_token={access_token}", json=payload)
        self._raise_if_errcode(data, "externalcontact.groupchat.statistic_group_by_day", required_keys=["items"])
        return data
