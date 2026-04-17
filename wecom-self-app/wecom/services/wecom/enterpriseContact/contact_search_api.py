"""通讯录相关 API（自建应用：使用应用 access_token，非服务商 contact/search）。"""
from typing import Any, Dict, List, Optional

from ..base import BaseClient, WeComApiError
from wecom.services.service import token_service


class EnterpriseContactApi(BaseClient):
    def search_contact(
        self,
        auth_corpid: str,
        query_word: str,
        access_token: Optional[str] = None,
        query_type: Optional[int] = None,
        query_range: Optional[int] = None,
        agentid: Optional[int] = None,
        limit: Optional[int] = None,
        full_match_field: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """按 userid 精确读取成员（user/get），兼容原 search 接口入参。

        原服务商 `service/contact/search` 在自建应用下不可用；此处将 `query_word` 视为 userid。
        """
        del query_type, query_range, agentid, limit, full_match_field, cursor
        token = access_token or token_service.get_corp_access_token(auth_corpid)
        if not token:
            raise WeComApiError("missing access_token")
        if not auth_corpid:
            raise WeComApiError("missing auth_corpid")
        if not query_word:
            raise WeComApiError("missing query_word")

        url = "https://qyapi.weixin.qq.com/cgi-bin/user/get"
        data = self._do_get(url, params={"access_token": token, "userid": query_word})
        self._raise_if_errcode(data, "user.get")
        return {"query_result": {"contact": data}}

    def batch_search_contact(
        self,
        auth_corpid: str,
        query_request_list: list,
        access_token: Optional[str] = None,
        agentid: Optional[int] = None,
    ) -> Dict[str, Any]:
        del agentid
        token = access_token or token_service.get_corp_access_token(auth_corpid)
        if not token:
            raise WeComApiError("missing access_token")
        if not auth_corpid:
            raise WeComApiError("missing auth_corpid")
        if not isinstance(query_request_list, list) or not query_request_list:
            raise WeComApiError("missing query_request_list")

        results: List[Dict[str, Any]] = []
        for req in query_request_list:
            if not isinstance(req, dict):
                continue
            qw = req.get("query_word") or req.get("userid")
            if not qw:
                continue
            row = self.search_contact(auth_corpid, str(qw), access_token=token)
            qr = row.get("query_result") or {}
            results.append({"query_result": qr})

        return {"query_result_list": results}

    def sort_userid(
        self,
        auth_corpid: str,
        useridlist: list,
        access_token: Optional[str] = None,
        sort_options: Optional[list] = None,
    ) -> Dict[str, Any]:
        del auth_corpid, access_token, sort_options
        if not isinstance(useridlist, list) or not useridlist:
            raise WeComApiError("missing useridlist")
        raise WeComApiError("自建应用不支持 service/contact/sort，请使用管理端或自建排序逻辑")


def get_enterprise_contact_api(session: Optional[Any] = None) -> EnterpriseContactApi:
    return EnterpriseContactApi(session=session)
