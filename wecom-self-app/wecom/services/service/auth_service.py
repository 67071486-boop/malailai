"""历史兼容：第三方应用「临时授权码换永久授权码」流程。

自建应用不再使用本模块；保留空实现以免旧脚本 import 报错。
"""
from typing import Optional, Tuple


def get_permanent_code(auth_code: str) -> Optional[Tuple[str, dict]]:
    print("[auth_service] 自建应用模式已忽略 get_permanent_code 调用 auth_code=", auth_code, flush=True)
    return None


def async_get_permanent_code(auth_code: str) -> None:
    get_permanent_code(auth_code)


__all__ = ["get_permanent_code", "async_get_permanent_code"]
