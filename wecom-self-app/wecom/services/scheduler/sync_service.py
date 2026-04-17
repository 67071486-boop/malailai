from typing import Optional
import hashlib
import time
from datetime import datetime, timezone, timedelta

from wecom.dao import (
    query_pending_orders,
    query_group_chat_by_name,
    mark_pending_done,
    upsert_group_chat,
    delete_expired_pending_orders,
    query_corp_configs_created_before,
    delete_corp_config_by_id,
    clear_group_chat_join_way,
    insert_observe_log,
)
from wecom.services.service import token_service
from wecom.services.wecom.kf.session_manager import KfSessionApi
from wecom.services.wecom.externalcontact.contact_way_manager import ContactWayApi
from wecom.services.biz.handlers.kf.config_cache import KfConfigCache
from wecom.services.biz.handlers.kf.sender import KfMessageSender
import config

# 这里放置主动同步实现（订单二维码自动推送）
DEFAULT_WELCOME_REPLY = "您好！我是群码自助机器人，请把订单号发给我获取二维码"
WELCOME_CACHE_TTL_SECONDS = 60


def _make_msgid(prefix: str, base: str) -> str:
    raw = f"{prefix}{base}"
    if len(raw) <= 32:
        return raw
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()
    if prefix:
        available = 32 - len(prefix)
        return f"{prefix}{digest[:available]}" if available > 0 else digest[:32]
    return digest[:32]


def sync_tick() -> None:
    """定时扫描待推送订单，若群已创建则发送二维码并绑定。"""
    insert_observe_log(
        category="scheduler",
        task="sync_tick",
        level="info",
        message="sync_tick start",
    )
    now = datetime.utcnow()
    delete_expired_pending_orders(now - timedelta(days=1))

    token_service.get_corp_access_token(config.WXWORK_CORP_ID)

    kf_api = KfSessionApi()
    sender = KfMessageSender(kf_api)
    contact_way_api = ContactWayApi()
    config_cache = KfConfigCache(WELCOME_CACHE_TTL_SECONDS, DEFAULT_WELCOME_REPLY)

    pending_list = query_pending_orders()
    if not pending_list:
        insert_observe_log(
            category="scheduler",
            task="sync_tick",
            level="info",
            message="no pending orders",
        )
        return None

    sent_count = 0
    for item in pending_list:
        corp_id = item.get("corp_id")
        order_no = item.get("order_no")
        external_userid = item.get("external_userid")
        open_kfid = item.get("open_kfid")
        if not corp_id or not order_no or not external_userid or not open_kfid:
            mark_pending_done(corp_id, order_no, external_userid, result="invalid")
            continue

        group_chat = query_group_chat_by_name(corp_id, order_no)
        if not group_chat:
            continue

        bound = group_chat.get("bound") if isinstance(group_chat.get("bound"), dict) else None
        bound_user = bound.get("external_userid") if bound else None
        if bound_user and bound_user != external_userid:
            mark_pending_done(corp_id, order_no, external_userid, result="taken")
            continue

        access_token = token_service.get_corp_access_token(corp_id or config.WXWORK_CORP_ID)
        if not access_token:
            continue

        chat_id = group_chat.get("chat_id")
        if not chat_id:
            continue

        join_way = group_chat.get("join_way") if isinstance(group_chat.get("join_way"), dict) else None
        qr_code = join_way.get("qr_code") if isinstance(join_way, dict) else None
        if not qr_code:
            try:
                payload = {
                    "scene": 2,
                    "remark": order_no,
                    "chat_id_list": [chat_id],
                }
                add_resp = contact_way_api.add_join_way(access_token, payload, corp_id=corp_id)
                join_way = add_resp.get("join_way") if isinstance(add_resp, dict) else None
                qr_code = join_way.get("qr_code") if isinstance(join_way, dict) else None
            except Exception:
                continue

        if not qr_code:
            continue

        msgid = _make_msgid("auto_", f"{order_no}")
        sent_qr = False
        try:
            sender.send_text_reply(
                access_token,
                open_kfid,
                external_userid,
                f"订单 {order_no} 的入群二维码：{qr_code}",
                msgid=msgid,
                msgid_prefix="",
            )
            now = datetime.now(timezone.utc)
            group_chat["bound"] = {
                "external_userid": external_userid,
                "order_no": order_no,
                "bound_at": now,
                "booster": None,
            }
            group_chat["updated_at"] = now
            upsert_group_chat(group_chat)
            mark_pending_done(corp_id, order_no, external_userid, result="sent")
            sent_qr = True
            sent_count += 1
        except Exception:
            insert_observe_log(
                category="scheduler",
                task="sync_tick",
                level="error",
                message="send qr failed",
                context={"corp_id": corp_id, "order_no": order_no, "external_userid": external_userid},
            )
            continue

        if sent_qr:
            time.sleep(0.5)
            config = config_cache.get_config(corp_id, open_kfid)
            if config and config.get("msgtype") == "msgmenu":
                payload = config.get("payload")
                if isinstance(payload, dict):
                    menu_payload = dict(payload)
                    menu_payload["head_content"] = "如需其他服务，请点击"
                    sender.send_reply_message(
                        access_token,
                        open_kfid,
                        external_userid,
                        ("msgmenu", menu_payload),
                        msgid=msgid,
                        msgid_prefix="menu_hint_",
                    )

    insert_observe_log(
        category="scheduler",
        task="sync_tick",
        level="info",
        message="sync_tick done",
        context={"pending": len(pending_list), "sent": sent_count},
    )


def sync_messages(corp_id: str, cursor: Optional[str] = None) -> None:
    """拉取消息的占位函数，后续实现调用企微消息存档接口。"""
    return None


def cleanup_expired_corp_configs() -> None:
    """清理超过 3 天的 corp_config_id 记录，并同步清空 group_chats join_way。"""
    expired_before = datetime.utcnow() - timedelta(days=3)
    configs = query_corp_configs_created_before(expired_before)
    if not configs:
        insert_observe_log(
            category="scheduler",
            task="cleanup_expired_corp_configs",
            level="info",
            message="no expired corp_config_id",
        )
        return None

    contact_way_api = ContactWayApi()
    deleted_count = 0

    for item in configs:
        config_id = item.get("config_id")
        corp_id = item.get("corp_id")
        join_way = item.get("join_way")
        chat_id = item.get("chat_id")

        if not join_way:
            continue
        if not config_id or not corp_id:
            continue

        access_token = token_service.get_corp_access_token(corp_id)
        if not access_token:
            continue

        try:
            contact_way_api.delete_contact_way(access_token, config_id)
        except Exception:
            insert_observe_log(
                category="scheduler",
                task="cleanup_expired_corp_configs",
                level="error",
                message="delete_contact_way failed",
                context={"corp_id": corp_id, "config_id": config_id},
            )
            continue

        delete_corp_config_by_id(config_id)
        if chat_id:
            clear_group_chat_join_way(chat_id)
        deleted_count += 1

    insert_observe_log(
        category="scheduler",
        task="cleanup_expired_corp_configs",
        level="info",
        message="cleanup done",
        context={"total": len(configs), "deleted": deleted_count},
    )


__all__ = ["sync_tick", "sync_messages", "cleanup_expired_corp_configs"]
