"""企业微信「客户联系」相关回调的业务占位实现。

当前仅占位，实际逻辑待补充：如处理 change_external_chat 创建群聊事件等。
"""
from typing import Dict, Optional
from ..dispatcher import BizHandler


class ContactEventHandler(BizHandler):
    HANDLED_TYPES = {
        "change_external_contact",
        "change_external_chat",
        "change_external_tag",
    }

    def can_handle(self, info_type: Optional[str], payload: Dict) -> bool:
        return info_type in self.HANDLED_TYPES

    def handle(self, info_type: Optional[str], payload: Dict, *, receive_id: Optional[str], source: str) -> None:
        # TODO: 在此处编写客户联系相关的业务逻辑，例如：
        # - change_external_chat: 企业新建群聊回调，提取 ChatId 等信息并落库
        # - change_external_contact: 客户联系人变更
        # - change_external_tag: 外部联系人标签变更
        print(
            "[biz.contact] received",
            info_type,
            "source=", source,
            "receive_id=", receive_id,
            flush=True,
        )
