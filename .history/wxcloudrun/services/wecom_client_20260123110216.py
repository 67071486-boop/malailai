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

依赖：requests, tenacity（可选重试）
"""
from typing import Any, Dict, Optional
import time
import requests
from wxcloudrun.services.token_service import get_suite_access_token


class WeComApiError(Exception):
    """表示企业微信 API 返回 errcode != 0 的错误。"""


class BaseClient:
    def __init__(self, session: Optional[requests.Session] = None, timeout: int = 10):
        self.session = session or requests.Session()
        self.timeout = timeout

    @staticmethod
    def _raise_if_errcode(data: Dict[str, Any], ctx: str = "", required_keys: Optional[list] = None):
        """检查返回：
        - 如果返回不是 dict 报错
        - 如果包含 errcode：errcode!=0 抛错
        - 如果不包含 errcode：
            - 若提供 required_keys，检查字段存在性并在缺失时抛错
            - 否则打印警告并按成功处理（兼容历史接口行为）
        """
        if not isinstance(data, dict):
            raise WeComApiError(f"Invalid response format for {ctx}: {data}")
        # 明确返回 errcode 时按规范处理
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

    def _get(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        attempts = 3
        for i in range(attempts):
            try:
                resp = self.session.get(url, params=params or {}, timeout=self.timeout)
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException:
                if i == attempts - 1:
                    raise
                time.sleep(1)

    def _post(self, url: str, json: Dict[str, Any] = None) -> Dict[str, Any]:
        attempts = 3
        for i in range(attempts):
            try:
                resp = self.session.post(url, json=json or {}, timeout=self.timeout)
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException:
                if i == attempts - 1:
                    raise
                time.sleep(1)


class SuiteClient(BaseClient):
    """第三方应用相关 API 封装（suite_access_token, get_permanent_code, getuserinfo3rd 等）"""

    def get_suite_access_token(self) -> Optional[str]:
        # 复用现有 token_service 缓存逻辑
        return get_suite_access_token()

    def get_permanent_code(self, auth_code: str) -> Dict[str, Any]:
        """通过临时 auth_code 获取永久授权码（并返回完整响应）"""
        token = self.get_suite_access_token()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_permanent_code"
        params = {"suite_access_token": token}
        data = self._post(url + f"?suite_access_token={token}", json={"auth_code": auth_code})
        self._raise_if_errcode(data, "get_permanent_code")
        return data

    def getuserinfo3rd(self, code: str) -> Dict[str, Any]:
        token = self.get_suite_access_token()
        if not token:
            raise WeComApiError("missing suite_access_token")
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/getuserinfo3rd"
        data = self._get(url, params={"suite_access_token": token, "code": code})
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
        data = self._post(url + f"?suite_access_token={token}", json=payload)
        self._raise_if_errcode(data, "get_corp_access_token")
        return data

    def send_message(self, corp_access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
        data = self._post(url + f"?access_token={corp_access_token}", json=payload)
        self._raise_if_errcode(data, "send_message")
        return data

    def get_user(self, corp_access_token: str, userid: str) -> Dict[str, Any]:
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/get"
        data = self._get(url, params={"access_token": corp_access_token, "userid": userid})
        self._raise_if_errcode(data, "get_user")
        return data

    def get_department(self, corp_access_token: str, dept_id: int) -> Dict[str, Any]:
        url = "https://qyapi.weixin.qq.com/cgi-bin/department/get"
        data = self._get(url, params={"access_token": corp_access_token, "id": dept_id})
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
