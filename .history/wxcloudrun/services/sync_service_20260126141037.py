from typing import Optional
import hashlib
from datetime import datetime, timezone

from wxcloudrun.dao import (
    query_pending_orders,
    query_group_chat_by_name,
    query_corp_auth,
    mark_pending_done,
    upsert_group_chat,
)
from wxcloudrun.services import token_service
from wxcloudrun.services.wecom.kf.session_manager import KfSessionApi
from wxcloudrun.services.wecom.externalcontact.contact_way_manager import ContactWayApi

# 这里放置主动同步实现（订单二维码自动推送）


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
    pending_list = query_pending_orders(limit=100)
    if not pending_list:
        return None

    kf_api = KfSessionApi()
    contact_way_api = ContactWayApi()

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

        bound_user = group_chat.get("bound_external_userid")
        if bound_user and bound_user != external_userid:
            mark_pending_done(corp_id, order_no, external_userid, result="taken")
            continue

        corp_auth = query_corp_auth(corp_id)
        if not corp_auth or not corp_auth.get("permanent_code"):
            continue

        access_token = token_service.get_corp_access_token(corp_id, corp_auth["permanent_code"])
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

        msgid = _make_msgid("auto_", f"{corp_id}-{order_no}")
        payload = {
            "touser": external_userid,
            "open_kfid": open_kfid,
            "msgtype": "text",
            "text": {"content": f"订单 {order_no} 的入群二维码：{qr_code}"},
            "msgid": msgid,
        }
        try:
            kf_api.send_message(access_token, payload)
            now = datetime.now(timezone.utc)
            group_chat["bound_external_userid"] = external_userid
            group_chat["bound_at"] = now
            group_chat["bound_order_no"] = order_no
            group_chat["updated_at"] = now
            upsert_group_chat(group_chat)
            mark_pending_done(corp_id, order_no, external_userid, result="sent")
        except Exception:
            continue


def sync_messages(corp_id: str, cursor: Optional[str] = None) -> None:
    """拉取消息的占位函数，后续实现调用企微消息存档接口。"""
    return None


def sync_contacts(corp_id: str) -> None:
    """拉取通讯录的占位函数。"""
    return None


__all__ = ["sync_tick", "sync_messages", "sync_contacts"]
