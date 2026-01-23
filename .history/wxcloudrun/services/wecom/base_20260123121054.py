"""WeCom API 基础客户端与错误定义。"""
from typing import Any, Dict, List, Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential  # type: ignore


class WeComApiError(Exception):
    """表示企业微信 API 或网络/解析错误。"""


class BaseClient:
    def __init__(self, session: Optional[requests.Session] = None, timeout: int = 10):
        self.session = session or requests.Session()
        self.timeout = timeout

    @staticmethod
    def _raise_if_errcode(data: Dict[str, Any], ctx: str = "", required_keys: Optional[List[str]] = None):
        """统一 errcode 判定与必要字段校验。"""
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
            raise WeComApiError(f"HTTP GET failed for {url}: {exc}")
        except ValueError as exc:
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
