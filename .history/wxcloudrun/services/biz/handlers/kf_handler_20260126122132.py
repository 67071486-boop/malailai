"""企业微信「微信客服」回调业务处理骨架。

核心策略：
- 回调仅作为“触发器”，不直接处理消息体，避免并发触发导致重复回复。
- 按 open_kfid 级别串行拉取消息（短 TTL 进程锁），依赖 next_cursor 做增量拉取。
- 消息入库/幂等后再分发到业务处理（当前占位）。
"""
import threading
import hashlib
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, Any

from ..dispatcher import BizHandler
from wxcloudrun.dao import (
    query_corp_auth,
    query_kf_cursor,
    upsert_kf_cursor,
    query_group_chat_by_name,
    query_corp_config_by_chat,
    upsert_corp_config,
    upsert_group_chat,
)
from wxcloudrun.model import new_kf_cursor
from wxcloudrun.services import token_service
from wxcloudrun.services.wecom.kf.session_manager import KfSessionApi
from wxcloudrun.services.wecom.externalcontact.contact_way_manager import ContactWayApi


class KfEventHandler(BizHandler):
    HANDLED_TYPES = {"kf_msg_or_event"}

    def __init__(self):
        # 简单进程内锁，生产建议换成 Redis 分布式锁防止多实例并发拉取。
        self._lock = threading.Lock()
        self._pulling = set()
        self._session_api = KfSessionApi()
        self._contact_way_api = ContactWayApi()

    def can_handle(self, evt_type: Optional[str], payload: Dict) -> bool:
        return evt_type in self.HANDLED_TYPES

    def handle(self, evt_type: Optional[str], payload: Dict, *, receive_id: Optional[str], source: str) -> None:
        xml = payload.get("xml", {}) if isinstance(payload, dict) else {}
        open_kfid = xml.get("OpenKfId")
        corp_id = xml.get("ToUserName") or receive_id
        if not open_kfid:
            print("[biz.kf] missing OpenKfId", xml, flush=True)
            return

        if not corp_id:
            print("[biz.kf] missing corp_id", xml, flush=True)
            return

        corp_auth = query_corp_auth(corp_id)
        if not corp_auth or not corp_auth.get("permanent_code"):
            print("[biz.kf] corp_auth not found for", corp_id, flush=True)
            return

        access_token = token_service.get_corp_access_token(corp_id, corp_auth["permanent_code"])
        if not access_token:
            print("[biz.kf] access_token unavailable for", corp_id, flush=True)
            return

        # 回调触发拉取流程；真实消息内容由后续拉取接口获取。
        self._schedule_pull(open_kfid, access_token, corp_id)

    # === 拉取与锁控制 ===
    def _schedule_pull(self, open_kfid: str, access_token: str, corp_id: str) -> None:
        if not self._acquire(open_kfid):
            print("[biz.kf] pull skipped, already running", open_kfid, flush=True)
            return
        try:
            cursor = self._load_next_cursor(open_kfid)
            self._pull_and_process(open_kfid, cursor, access_token, corp_id)
        finally:
            self._release(open_kfid)

    def _acquire(self, open_kfid: str) -> bool:
        with self._lock:
            if open_kfid in self._pulling:
                return False
            self._pulling.add(open_kfid)
            return True

    def _release(self, open_kfid: str) -> None:
        with self._lock:
            self._pulling.discard(open_kfid)

    # === 游标存取（需替换为持久化实现） ===
    def _load_next_cursor(self, open_kfid: str) -> Optional[str]:
        doc = query_kf_cursor(open_kfid)
        if not doc:
            return None
        return doc.get("cursor")

    def _save_next_cursor(self, open_kfid: str, cursor: Optional[str], corp_id: Optional[str] = None) -> None:
        if not cursor:
            return
        doc = query_kf_cursor(open_kfid)
        if doc:
            doc["cursor"] = cursor
            doc["updated_at"] = datetime.now(timezone.utc)
        else:
            doc = new_kf_cursor(open_kfid, cursor, corp_id=corp_id)
        upsert_kf_cursor(doc)

    # === 消息拉取与处理 ===
    def _pull_and_process(self, open_kfid: str, cursor: Optional[str], access_token: str, corp_id: str) -> None:
        next_cursor = cursor
        while True:
            resp = self._fetch_messages(open_kfid, next_cursor, access_token)
            if not resp:
                return

            msg_list = resp.get("msg_list") or []
            for msg in msg_list:
                self._handle_message(msg, access_token, corp_id)

            # 更新游标，优先使用返回值；若无返回则保留原值。
            next_cursor = resp.get("next_cursor") or next_cursor
            if next_cursor is not None:
                self._save_next_cursor(open_kfid, next_cursor, corp_id)

            if not resp.get("has_more"):
                break

    def _fetch_messages(self, open_kfid: str, cursor: Optional[str], access_token: str):
        """调用微信客服拉取消息接口，返回 msg_list/next_cursor/has_more。"""
        try:
            resp = self._session_api.sync_msg(access_token, open_kfid, cursor=cursor)
            return resp
        except Exception as exc:
            print("[biz.kf] fetch messages failed", open_kfid, "cursor=", cursor, "err=", exc, flush=True)
            return None

    # === 单条消息处理 ===
    def _handle_message(self, msg: Dict, access_token: str, corp_id: str) -> None:
        msgtype, payload, raw = self._extract_message_payload(msg)
        if msgtype == "text":
            self._handle_text(raw, payload, access_token, corp_id)
        elif msgtype == "event":
            self._handle_event(raw, payload, access_token)
        else:
            print("[biz.kf] unsupported msgtype", msgtype, "msgid=", msg.get("msgid"), flush=True)

    def _extract_message_payload(self, msg: Dict) -> Tuple[Optional[str], Optional[Dict[str, Any]], Dict]:
        """兼容 msgtype 可能是字符串或结构体的两种格式。"""
        msgtype = msg.get("msgtype")
        if isinstance(msgtype, dict):
            inner = msgtype
            inner_type = inner.get("msgtype")
            inner_payload = inner.get(inner_type) if inner_type else None
            return inner_type, inner_payload, msg
        if isinstance(msgtype, str):
            payload = msg.get(msgtype) if isinstance(msg.get(msgtype), dict) else None
            return msgtype, payload, msg
        return None, None, msg

    def _handle_text(self, msg: Dict, payload: Optional[Dict[str, Any]], access_token: str, corp_id: str) -> None:
        content = None
        if payload and isinstance(payload, dict):
            content = payload.get("content")
        elif isinstance(msg.get("text"), dict):
            content = msg.get("text", {}).get("content")
        print("[biz.kf] text message", "msgId=" + str(msg.get("msgid")), "内容=" + str(content), flush=True)
    
        if not content or not isinstance(content, str):
            return

        order_no = content.strip()
        is_order_no = order_no.isdigit() and len(order_no) >= 16

        open_kfid = msg.get("open_kfid")
        external_userid = msg.get("external_userid")
        if not open_kfid or not external_userid:
            print("[biz.kf] missing open_kfid/external_userid", msg.get("msgid"), flush=True)
            return

        if not is_order_no:
            self._send_text_reply(
                access_token,
                open_kfid,
                external_userid,
                "查询失败，请输入有效的订单号",
                msgid=msg.get("msgid"),
                msgid_prefix="invalid_",
            )
            return

        group_chat = query_group_chat_by_name(corp_id, order_no)
        if not group_chat:
            reply = f"未找到订单 {order_no} 对应的群信息"
        else:
            chat_id = group_chat.get("chat_id")
            if not chat_id:
                reply = f"订单 {order_no} 对应群缺少 chat_id，无法生成二维码"
                self._send_text_reply(
                    access_token,
                    open_kfid,
                    external_userid,
                    reply,
                    msgid=msg.get("msgid"),
                    msgid_prefix="order_",
                )
                return

            join_way = group_chat.get("join_way") if isinstance(group_chat.get("join_way"), dict) else None
            if not join_way:
                config_doc = query_corp_config_by_chat(corp_id, chat_id)
                if config_doc and isinstance(config_doc.get("join_way"), dict):
                    join_way = config_doc.get("join_way")

            qr_code = join_way.get("qr_code") if isinstance(join_way, dict) else None
            if not qr_code:
                try:
                    payload = {
                        "scene": 2,
                        "remark": order_no,
                        "chat_id_list": [chat_id],
                    }
                    add_resp = self._contact_way_api.add_join_way(access_token, payload)
                    config_id = add_resp.get("config_id")
                    if not config_id:
                        raise ValueError("missing config_id from add_join_way")

                    join_resp = self._contact_way_api.get_join_way(access_token, config_id)
                    join_way = join_resp.get("join_way") if isinstance(join_resp, dict) else None
                    qr_code = join_way.get("qr_code") if isinstance(join_way, dict) else None

                    now = datetime.now(timezone.utc)
                    upsert_corp_config(
                        {
                            "corp_id": corp_id,
                            "chat_id": chat_id,
                            "config_id": config_id,
                            "join_way": join_way,
                            "contact_way": None,
                            "updated_at": now,
                            "created_at": now,
                        }
                    )

                    group_chat["join_way"] = join_way
                    group_chat["join_way_config_id"] = config_id
                    group_chat["updated_at"] = now
                    upsert_group_chat(group_chat)
                except Exception as exc:
                    print("[biz.kf] add_join_way failed", order_no, "err=", exc, flush=True)

            if qr_code:
                reply = f"订单 {order_no} 的入群二维码：{qr_code}"
            else:
                reply = f"订单 {order_no} 暂无法生成二维码，请稍后再试"

        self._send_text_reply(
            access_token,
            open_kfid,
            external_userid,
            reply,
            msgid=msg.get("msgid"),
            msgid_prefix="order_",
        )

    def _send_text_reply(
        self,
        access_token: str,
        open_kfid: str,
        external_userid: str,
        content: str,
        *,
        msgid: Optional[str] = None,
        msgid_prefix: str = "",
    ) -> None:
        payload = {
            "touser": external_userid,
            "open_kfid": open_kfid,
            "msgtype": "text",
            "text": {"content": content},
        }
        if msgid:
            combined = f"{msgid_prefix}{msgid}"
            if len(combined) > 32:
                digest = hashlib.md5(combined.encode("utf-8")).hexdigest()
                if msgid_prefix:
                    available = 32 - len(msgid_prefix)
                    if available > 0:
                        combined = f"{msgid_prefix}{digest[:available]}"
                    else:
                        combined = digest[:32]
                else:
                    combined = digest[:32]
            payload["msgid"] = combined

        try:
            self._session_api.send_message(access_token, payload)
        except Exception as exc:
            print("[biz.kf] send_message failed", msgid, "err=", exc, flush=True)

    def _handle_event(self, msg: Dict, payload: Optional[Dict[str, Any]], access_token: str) -> None:
        event_payload = payload if isinstance(payload, dict) else (msg.get("event") or {})
        event = event_payload.get("event_type")
        if event == "enter_session":
            self._on_enter_session(msg, event_payload, access_token)
        elif event == "msg_send_fail":
            self._on_msg_send_fail(msg)
        elif event == "servicer_status_change":
            self._on_servicer_status_change(msg)
        elif event == "session_status_change":
            self._on_session_status_change(msg)
        elif event == "user_recall_msg":
            self._on_user_recall(msg)
        elif event == "servicer_recall_msg":
            self._on_servicer_recall(msg)
        elif event == "reject_customer_msg_switch_change":
            self._on_reject_switch_change(msg)
        else:
            print("[biz.kf] unsupported event_type", event, "msgid=", msg.get("msgid"), flush=True)

    # === 各事件占位 ===
    def _on_enter_session(self, msg: Dict, payload: Dict, access_token: str) -> None:
        welcome_code = payload.get("welcome_code")
        if not welcome_code:
            print("[biz.kf] enter_session missing welcome_code", msg.get("msgid"), flush=True)
            return

        reply = "您好！我是群码自助机器人，请把订单号发给我获取二维码"
        payload = {
            "code": welcome_code,
            "msgtype": "text",
            "text": {"content": reply},
        }
        try:
            self._session_api.send_msg_on_event(access_token, payload)
        except Exception as exc:
            print("[biz.kf] send_msg_on_event failed", msg.get("msgid"), "err=", exc, flush=True)

    def _on_msg_send_fail(self, msg: Dict) -> None:
        # TODO: 发送失败补偿/告警。
        print("[biz.kf] msg_send_fail", msg.get("msgid"), flush=True)

    def _on_servicer_status_change(self, msg: Dict) -> None:
        # TODO: 客服状态变更处理。
        print("[biz.kf] servicer_status_change", msg.get("msgid"), flush=True)

    def _on_session_status_change(self, msg: Dict) -> None:
        # TODO: 会话状态变更处理。
        print("[biz.kf] session_status_change", msg.get("msgid"), flush=True)

    def _on_user_recall(self, msg: Dict) -> None:
        # TODO: 用户撤回消息处理。
        print("[biz.kf] user_recall_msg", msg.get("msgid"), flush=True)

    def _on_servicer_recall(self, msg: Dict) -> None:
        # TODO: 客服撤回消息处理。
        print("[biz.kf] servicer_recall_msg", msg.get("msgid"), flush=True)

    def _on_reject_switch_change(self, msg: Dict) -> None:
        # TODO: 拒收开关变更处理。
        print("[biz.kf] reject_customer_msg_switch_change", msg.get("msgid"), flush=True)
