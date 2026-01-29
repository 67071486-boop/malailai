"""企业微信服务商通讯录搜索 API（单个搜索）。"""
from typing import Any, Dict, Optional

from ..base import BaseClient, WeComApiError


class EnterpriseContactApi(BaseClient):
    def search_contact(
        self,
        provider_access_token: str,
        auth_corpid: str,
        query_word: str,
        query_type: Optional[int] = None,
        query_range: Optional[int] = None,
        agentid: Optional[int] = None,
        limit: Optional[int] = None,
        full_match_field: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """通讯录单个搜索（服务商）。

        POST https://qyapi.weixin.qq.com/cgi-bin/service/contact/search?provider_access_token=ACCESS_TOKEN
        """
        if not provider_access_token:
            raise WeComApiError("missing provider_access_token")
        if not auth_corpid:
            raise WeComApiError("missing auth_corpid")
        if not query_word:
            raise WeComApiError("missing query_word")

        url = "https://qyapi.weixin.qq.com/cgi-bin/service/contact/search"
        payload: Dict[str, Any] = {
            "auth_corpid": auth_corpid,
            "query_word": query_word,
        }
        if query_type is not None:
            payload["query_type"] = query_type
        if query_range is not None:
            payload["query_range"] = query_range
        if agentid is not None:
            payload["agentid"] = agentid
        if limit is not None:
            payload["limit"] = limit
        if full_match_field is not None:
            payload["full_match_field"] = full_match_field
        if cursor:
            payload["cursor"] = cursor

        data = self._do_post(url + f"?provider_access_token={provider_access_token}", json=payload)
        self._raise_if_errcode(data, "enterprise_contact_search")
        return data

    def batch_search_contact(
        self,
        provider_access_token: str,
        auth_corpid: str,
        query_request_list: list,
        agentid: Optional[int] = None,
    ) -> Dict[str, Any]:
        """通讯录批量搜索（服务商）。

        POST https://qyapi.weixin.qq.com/cgi-bin/service/contact/batchsearch?provider_access_token=ACCESS_TOKEN
        """
        if not provider_access_token:
            raise WeComApiError("missing provider_access_token")
        if not auth_corpid:
            raise WeComApiError("missing auth_corpid")
        if not isinstance(query_request_list, list) or not query_request_list:
            raise WeComApiError("missing query_request_list")

        url = "https://qyapi.weixin.qq.com/cgi-bin/service/contact/batchsearch"
        payload: Dict[str, Any] = {
            "auth_corpid": auth_corpid,
            "query_request_list": query_request_list,
        }
        if agentid is not None:
            payload["agentid"] = agentid

        data = self._do_post(url + f"?provider_access_token={provider_access_token}", json=payload)
        self._raise_if_errcode(data, "enterprise_contact_batch_search")
        return data

    def sort_userid(
        self,
        provider_access_token: str,
        auth_corpid: str,
        useridlist: list,
        sort_options: Optional[list] = None,
    ) -> Dict[str, Any]:
        """通讯录 userid 排序（服务商）。"""
        if not provider_access_token:
            raise WeComApiError("missing provider_access_token")
        if not auth_corpid:
            raise WeComApiError("missing auth_corpid")
        if not isinstance(useridlist, list) or not useridlist:
            raise WeComApiError("missing useridlist")

        url = "https://qyapi.weixin.qq.com/cgi-bin/service/contact/sort"
        payload: Dict[str, Any] = {
            "auth_corpid": auth_corpid,
            "useridlist": useridlist,
        }
        if sort_options:
            payload["sort_options"] = sort_options

        data = self._do_post(url + f"?provider_access_token={provider_access_token}", json=payload)
        self._raise_if_errcode(data, "enterprise_contact_sort")
        return data


def get_enterprise_contact_api(session: Optional[Any] = None) -> EnterpriseContactApi:
    return EnterpriseContactApi(session=session)
