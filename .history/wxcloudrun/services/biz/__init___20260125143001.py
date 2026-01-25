"""业务层入口：集中管理各类回调事件的分发与处理。

biz_dispatcher 用于把企业微信回调解密后的 payload 路由到具体业务 handler。
"""
from .dispatcher import BizDispatcher
from .handlers.contact_event_handler import ContactEventHandler
from .handlers.kf_handler import KfEventHandler
from .handlers.externalcontact_handler import ContactEventHandler as ExternalContactEventHandler

# 全局 dispatcher，按需注册 handler（可扩展更多业务模块）。
biz_dispatcher = BizDispatcher([
    ContactEventHandler(),            # 旧占位（保留兼容）
    ExternalContactEventHandler(),    # 客户联系回调
    KfEventHandler(),
])

__all__ = ["biz_dispatcher", "BizDispatcher"]
