"""WeCom API 客户端封装

提供 SuiteClient（第三方应用）与 CorpClient（企业侧）的基本封装。
- 使用 requests.Session 复用连接
- 统一封装请求、errcode 判定、抛出 WeComApiError
- 与现有 token_service 协作获取并复用 token

常用方法示例：
- SuiteClient.get_permanent_code(auth_code)
- SuiteClient.getuserinfo3rd(code)
- SuiteClient.get_suite_access_token()
- CorpClient.get_corp_access_token(corp_id, permanent_code)
- CorpClient.send_message(corp_id, agentid, payload)

依赖：requests, tenacity（用于重试）
"""
from typing import Any, Dict, Optional, List
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential # type: ignore
from wxcloudrun.services import token_cache


class WeComApiError(Exception):
    """表示企业微信 API 错误或网络/解析失败。"""


class BaseClient:
    def __init__(self, session: Optional[requests.Session] = None, timeout: int = 10):
        self.session = session or requests.Session()
        self.timeout = timeout

    @staticmethod
    def _raise_if_errcode(data: Dict[str, Any], ctx: str = "", required_keys: Optional[List[str]] = None):
        """检查返回：
        - 如果返回不是 dict 报错
        - 如果包含 errcode：errcode!=0 抛错
        - 如果不包含 errcode：
            - 若提供 required_keys，检查字段存在性并在缺失时抛错
            - 否则打印警告并按成功处理（兼容历史接口行为）
        """
        if not isinstance(data, dict):
            raise WeComApiError(f"Invalid response format for {ctx}: {data}")
        if "errcode" in data:
            if data.get("errcode", 0) != 0:
                raise WeComApiError(f"WeCom API error for {ctx}: {data}")
            return
        # 无 errcode 的历史兼容处理
        if required_keys:
            missing = [k for k in required_keys if k not in data]
            if missing:
                raise WeComApiError(f"WeCom API {ctx} missing keys: {missing} resp={data}")
            return
        # 无 errcode 且未指定 required_keys：打印警告并当作成功
        print(f"[wecom_client] 警告：{ctx} 未返回 errcode，按成功处理 resp_keys={list(data.keys())}", flush=True)
        return

    def _do_get(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
        def _call():
            resp = self.session.get(url, params=params or {}, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()

        try:
            return _call()
        except requests.RequestException as e:
            raise WeComApiError(f"HTTP GET failed for {url}: {e}")
        except ValueError as e:
            raise WeComApiError(f"Invalid JSON response for GET {url}: {e}")

    def _do_post(self, url: str, json: Dict[str, Any] = None) -> Dict[str, Any]:
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
        def _call():
            resp = self.session.post(url, json=json or {}, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()

        try:
            return _call()
        except requests.RequestException as e:
            raise WeComApiError(f"HTTP POST failed for {url}: {e}")
        except ValueError as e:
            raise WeComApiError(f"Invalid JSON response for POST {url}: {e}")


class SuiteClient(BaseClient):
    """第三方应用相关 API 封装（suite_access_token, get_permanent_code, getuserinfo3rd 等）"""

    def get_suite_access_token(self) -> Optional[str]:
        # 复用 token_cache 的缓存逻辑
        return token_cache.get_suite_access_token()

    def get_permanent_code(self, auth_code: str) -> Dict[str, Any]:
        """通过临时 auth_code 获取永久授权码（并返回完整响应）"""
        token = self.get_suite_access_token()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_permanent_code"
        data = self._do_post(url + f"?suite_access_token={token}", json={"auth_code": auth_code})
        # 需要返回 permanent_code 和 auth_corp_info
        self._raise_if_errcode(data, "get_permanent_code", required_keys=["permanent_code", "auth_corp_info"])
        return data


    # 辅助：低级别直接请求，用于 token_service 调用以获取 suite_access_token
    def fetch_suite_access_token(self, ticket: str) -> Dict[str, Any]:
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_suite_token"
        payload = {
            "suite_id": None,
            "suite_secret": None,
            "suite_ticket": ticket,
        }
        # 具体的 suite_id/suite_secret 不从这里读取，以便外部在请求前填充
        return self._do_post(url, json=payload)


def fetch_suite_access_token(ticket: str, suite_id: str, suite_secret: str) -> Dict[str, Any]:
    """独立函数：通过 suite_ticket 拉取 suite_access_token 并返回原始响应。"""
    url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_suite_token"
    payload = {"suite_id": suite_id, "suite_secret": suite_secret, "suite_ticket": ticket}
    client = SuiteClient()
    data = client._do_post(url, json=payload)
    SuiteClient._raise_if_errcode(data, "fetch_suite_access_token", required_keys=["suite_access_token", "expires_in"])
    # 保存到 cache
    token = data.get("suite_access_token")
    expires = int(data.get("expires_in", 7200))
    token_cache.save_suite_access_token(token, expires)
    return data


def fetch_corp_access_token(corp_id: str, permanent_code: str, suite_id: str) -> Dict[str, Any]:
    """通过 permanent_code 获取企业 access_token（用于 token_service 调用）。"""
    token = token_cache.get_suite_access_token()
    if not token:
        raise WeComApiError("missing suite_access_token")
    url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_corp_token"
    payload = {"auth_corpid": corp_id, "permanent_code": permanent_code, "suite_id": suite_id}
    client = SuiteClient()
    data = client._do_post(url + f"?suite_access_token={token}", json=payload)
    SuiteClient._raise_if_errcode(data, "fetch_corp_access_token", required_keys=["access_token", "expires_in"])
    # 保存到 cache
    token_cache.save_corp_token(corp_id, data.get("access_token"), int(data.get("expires_in", 7200)))
    return data

    def getuserinfo3rd(self, code: str) -> Dict[str, Any]:
        token = self.get_suite_access_token()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/getuserinfo3rd"
        data = self._do_get(url, params={"suite_access_token": token, "code": code})
        self._raise_if_errcode(data, "getuserinfo3rd")
        return data


class CorpClient(BaseClient):
    """企业侧 API 封装（使用 permanent_code 换取 corp_access_token，企业接口等）

    说明：token 缓存策略可以继续留给 `token_service` 管理，本类提供对 API 的直接调用。
    """

    def get_corp_access_token(self, suite_id: str, corp_id: str, permanent_code: str) -> Dict[str, Any]:
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_corp_token"
        payload = {
            "auth_corpid": corp_id,
            "permanent_code": permanent_code,
            "suite_id": suite_id,
        }
        # 该接口需要 suite_access_token
        token = get_suite_access_token()
        if not token:
            raise WeComApiError("missing suite_access_token")
        data = self._do_post(url + f"?suite_access_token={token}", json=payload)
        self._raise_if_errcode(data, "get_corp_access_token", required_keys=["access_token"])
        return data

    def send_message(self, corp_access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
        data = self._do_post(url + f"?access_token={corp_access_token}", json=payload)
        self._raise_if_errcode(data, "send_message")
        return data

    def get_user(self, corp_access_token: str, userid: str) -> Dict[str, Any]:
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/get"
        data = self._do_get(url, params={"access_token": corp_access_token, "userid": userid})
        self._raise_if_errcode(data, "get_user")
        return data

    def get_department(self, corp_access_token: str, dept_id: int) -> Dict[str, Any]:
        url = "https://qyapi.weixin.qq.com/cgi-bin/department/get"
        data = self._do_get(url, params={"access_token": corp_access_token, "id": dept_id})
        self._raise_if_errcode(data, "get_department")
        return data


# 简单工厂/快捷函数
_default_suite_client: Optional[SuiteClient] = None


def get_suite_client() -> SuiteClient:
    global _default_suite_client
    if _default_suite_client is None:
        _default_suite_client = SuiteClient()
    return _default_suite_client


def get_corp_client() -> CorpClient:
    return CorpClient()
