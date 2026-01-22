from typing import Optional

# 这里放置主动同步占位实现，后续可扩展调用企微接口拉取消息/通讯录

def sync_tick() -> None:
    """占位任务，用于验证调度器是否运行。"""
    return None


def sync_messages(corp_id: str, cursor: Optional[str] = None) -> None:
    """拉取消息的占位函数，后续实现调用企微消息存档接口。"""
    return None


def sync_contacts(corp_id: str) -> None:
    """拉取通讯录的占位函数。"""
    return None


__all__ = ["sync_tick", "sync_messages", "sync_contacts"]
