"""企业微信「微信客服」回调的业务占位实现。

当前仅占位，实际逻辑待补充：如处理 kf_msg_or_event 的消息、分配、结束等事件。
"""
from typing import Dict, Optional
from ..dispatcher import BizHandler


class KfEventHandler(BizHandler):
    HANDLED_TYPES = {
        "kf_msg_or_event",
    }

    def can_handle(self, evt_type: Optional[str], payload: Dict) -> bool:
        return evt_type in self.HANDLED_TYPES

    def handle(self, evt_type: Optional[str], payload: Dict, *, receive_id: Optional[str], source: str) -> None:
        # TODO: 在此处编写微信客服相关的业务逻辑，例如：
        # - kf_msg_or_event: 消息收发、分配/接入/结束等事件
        print(
            "[biz.kf] received",
            evt_type,
            "source=", source,
            "receive_id=", receive_id,
            flush=True,
        )
