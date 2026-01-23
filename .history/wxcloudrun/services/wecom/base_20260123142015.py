"""WeCom API 基础客户端与错误定义。

本模块提供一个轻量的 HTTP 客户端封装，包含带重试的 GET/POST 方法、
统一的 errcode 检查与用于上层抛错的 `WeComApiError`。
所有对外 API 调用应继承 `BaseClient` 并使用本模块提供的 `_do_get/_do_post`。
"""
from typing import Any, Dict, List, Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential  # type: ignore


class WeComApiError(Exception):
    """表示企业微信 API 或网络/解析错误。

    上层在捕获此异常后可以根据需要重试或记录错误信息。
    """


class BaseClient:
    def __init__(self, session: Optional[requests.Session] = None, timeout: int = 10):
        self.session = session or requests.Session()
        self.timeout = timeout

    @staticmethod
    def _raise_if_errcode(data: Dict[str, Any], ctx: str = "", required_keys: Optional[List[str]] = None):
                """统一 errcode 判定与必要字段校验。

                - 如果返回为非 dict，则直接抛出异常。
                - 若存在 `errcode` 字段并且不为 0，则抛出 `WeComApiError`。
                - 当未提供 `errcode` 时，可通过 `required_keys` 指定必须存在的字段，
                    若缺失则抛出异常；否则认为成功并打印警告。
                """
        if not isinstance(data, dict):
            raise WeComApiError(f"Invalid response format for {ctx}: {data}")
        if "errcode" in data:
            if data.get("errcode", 0) != 0:
                raise WeComApiError(f"WeCom API error for {ctx}: {data}")
            return
        if required_keys:
            missing = [key for key in required_keys if key not in data]
            if missing:
                raise WeComApiError(f"WeCom API {ctx} missing keys: {missing} resp={data}")
            return
        print(f"[wecom] warning: {ctx} no errcode, treat as success keys={list(data.keys())}", flush=True)

    def _do_get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
        def _call():
            resp = self.session.get(url, params=params or {}, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()

        try:
            return _call()
        except requests.RequestException as exc:
            # 网络或请求异常统一包装为 WeComApiError
            raise WeComApiError(f"HTTP GET failed for {url}: {exc}")
        except ValueError as exc:
            # JSON 解析异常
            raise WeComApiError(f"Invalid JSON response for GET {url}: {exc}")

    def _do_post(self, url: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
        def _call():
            resp = self.session.post(url, json=json or {}, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()

        try:
            return _call()
        except requests.RequestException as exc:
            raise WeComApiError(f"HTTP POST failed for {url}: {exc}")
        except ValueError as exc:
            raise WeComApiError(f"Invalid JSON response for POST {url}: {exc}")
