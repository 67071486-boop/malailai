"""企业微信「客户联系」业务 API 占位模块。

按功能分类的客户端占位，后续可逐步补充具体实现。
"""
from .staff_manager import ContactStaffApi
from .customer_manager import ContactCustomerApi
from .tag_manager import ContactTagApi
from .onjob_transfer import ContactOnjobTransferApi
from .resign_transfer import ContactResignTransferApi
from .group_chat_manager import ContactGroupChatApi
from .contact_way_manager import ContactWayApi
from .moments_manager import ContactMomentsApi
from .message_push_manager import ContactMessagePushApi
from .statistic_manager import ContactStatisticApi
from .sensitive_manager import ContactSensitiveManagerApi
from .media_manager import ContactMediaApi

__all__ = [
    "ContactStaffApi",
    "ContactCustomerApi",
    "ContactTagApi",
    "ContactOnjobTransferApi",
    "ContactResignTransferApi",
    "ContactGroupChatApi",
    "ContactWayApi",
    "ContactMomentsApi",
    "ContactMessagePushApi",
    "ContactStatisticApi",
    "ContactSensitiveManagerApi",
    "ContactMediaApi",
]
