"""统一的业务事件分发器。

将 InfoType 以及解密后的 payload 路由到已注册的 handler。
"""
from typing import Dict, List, Optional


class BizHandler:
    """业务 handler 接口定义。"""

    def can_handle(self, info_type: Optional[str], payload: Dict) -> bool:
        raise NotImplementedError

    def handle(self, info_type: Optional[str], payload: Dict, *, receive_id: Optional[str], source: str) -> None:
        raise NotImplementedError


class BizDispatcher:
    def __init__(self, handlers: List[BizHandler]):
        self.handlers = handlers

    def dispatch(self, info_type: Optional[str], payload: Dict, *, receive_id: Optional[str], source: str = "command") -> None:
        """遍历 handlers，匹配 InfoType 并调用对应业务处理。"""
        for handler in self.handlers:
            if not handler.can_handle(info_type, payload):
                continue
            try:
                handler.handle(info_type, payload, receive_id=receive_id, source=source)
            except Exception as exc:  # 保底，不影响回包
                print(
                    "[biz] handler error",
                    handler.__class__.__name__,
                    "info_type=", info_type,
                    "source=", source,
                    "error=", exc,
                    flush=True,
                )
