"""应用授权（第三方应用）相关接口封装。

包含：获取 pre_auth_code、获取永久授权码（代理到 SuiteApi）、
以及查询企业授权信息（v2 接口）。
本模块对外提供 `AppAuthApi` 类与便捷函数 `fetch_pre_auth_code`/`fetch_auth_info`。
"""
from typing import Any, Dict, Optional
from .base import BaseClient, WeComApiError
from .suite_api import SuiteApi
from wxcloudrun.services import token_service


class AppAuthApi(BaseClient):
    def __init__(self, session=None, timeout: int = 10):
        super().__init__(session=session, timeout=timeout)
        self._suite_api = SuiteApi(session=self.session, timeout=self.timeout)

    def get_pre_auth_code(self, suite_id: str) -> Dict[str, Any]:
        """向企业微信申请 pre_auth_code，供企业进入授权页使用。

        参数：`suite_id` 为第三方应用的 SuiteID。
        返回包含 `pre_auth_code`。
        """
        token = token_cache.get_suite_access_token()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_pre_auth_code"
        payload = {"suite_id": suite_id}
        data = self._do_post(url + f"?suite_access_token={token}", json=payload)
        self._raise_if_errcode(data, "get_pre_auth_code", required_keys=["pre_auth_code"])
        return data

    def get_permanent_code(self, auth_code: str) -> Dict[str, Any]:
        """通过 `auth_code` 获取 `permanent_code`，内部委托给 `SuiteApi.get_permanent_code`。

        返回的数据通常包含 `permanent_code` 与 `auth_corp_info`。
        """
        return self._suite_api.get_permanent_code(auth_code)

    def get_auth_info(self, auth_corpid: str, permanent_code: str) -> Dict[str, Any]:
        """调用企业微信 v2 `get_auth_info` 接口以获取企业授权详情。

        参数：企业 corp_id 与已获取到的 `permanent_code`。
        返回包含 `auth_corp_info`（企业信息）及授权应用信息等。
        """
        token = token_service.get_suite_access_token_cached()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/v2/get_auth_info"
        payload = {"auth_corpid": auth_corpid, "permanent_code": permanent_code}
        data = self._do_post(url + f"?suite_access_token={token}", json=payload)
        self._raise_if_errcode(data, "get_auth_info", required_keys=["auth_corp_info"])
        return data

    def get_corp_token(self, auth_corpid: str, permanent_code: str) -> Dict[str, Any]:
        """根据企业的 `auth_corpid` 和 `permanent_code` 获取该企业的 access_token。

        该接口用于第三方服务商在取得永久授权码后，向企业微信申请企业 access_token，
        获取到的 `access_token` 可用于后续调用企业接口（通讯录、消息等）。

        请求说明：POST https://qyapi.weixin.qq.com/cgi-bin/service/get_corp_token?suite_access_token=SUITE_ACCESS_TOKEN
        请求体：{"auth_corpid": auth_corpid, "permanent_code": permanent_code}

        返回示例包含 `access_token` 与 `expires_in`。
        """
        token = token_service.get_suite_access_token_cached()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_corp_token"
        payload = {"auth_corpid": auth_corpid, "permanent_code": permanent_code}
        data = self._do_post(url + f"?suite_access_token={token}", json=payload)
        self._raise_if_errcode(data, "get_corp_token", required_keys=["access_token", "expires_in"])
        return data

    def get_app_permissions(self, access_token: str) -> Dict[str, Any]:
        """获取指定应用的权限详情。

        请求地址：POST https://qyapi.weixin.qq.com/cgi-bin/agent/get_permissions?access_token=ACCESS_TOKEN

        参数说明：
        - `access_token`：代开发自建应用的 access_token 或第三方应用通过 `get_corp_token` 获取的企业 access_token。

        返回包含 `app_permissions` 列表，表示应用拥有的权限字符串。
        """
        if not access_token:
            raise WeComApiError("missing access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/agent/get_permissions"
        # 接口要求 POST，但 body 可为空
        data = self._do_post(url + f"?access_token={access_token}", json={})
        self._raise_if_errcode(data, "get_app_permissions", required_keys=["app_permissions"])
        return data


def fetch_pre_auth_code(
    suite_id: str,
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    client = AppAuthApi(session=session, timeout=timeout)
    data = client.get_pre_auth_code(suite_id)
    return data


def fetch_auth_info(
    auth_corpid: str,
    permanent_code: str,
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    client = AppAuthApi(session=session, timeout=timeout)
    return client.get_auth_info(auth_corpid, permanent_code)


def fetch_corp_token(
    auth_corpid: str,
    permanent_code: str,
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    """便捷函数：使用 `AppAuthApi` 获取企业 access_token 并返回响应数据。"""
    client = AppAuthApi(session=session, timeout=timeout)
    return client.get_corp_token(auth_corpid, permanent_code)


def fetch_app_permissions(
    access_token: str,
    *,
    session=None,
    timeout: int = 10,
) -> Dict[str, Any]:
    """便捷函数：使用 `AppAuthApi` 获取应用权限详情（app_permissions）。"""
    client = AppAuthApi(session=session, timeout=timeout)
    return client.get_app_permissions(access_token)
