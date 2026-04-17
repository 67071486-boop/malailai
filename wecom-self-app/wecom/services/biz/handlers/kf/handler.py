"""企业微信「微信客服」回调业务处理骨架。"""
import threading
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, Any

from ...dispatcher import BizHandler
from wecom.services.service import token_service
import config
from wecom.services.wecom.kf.session_manager import KfSessionApi
from wecom.services.wecom.kf.servicer_manager import KfStaffApi
from wecom.services.wecom.externalcontact.contact_way_manager import ContactWayApi
from .config_cache import KfConfigCache
from .cursor_store import KfCursorStore
from .order_flow import KfOrderProcessor
from .sender import KfMessageSender


class KfEventHandler(BizHandler):
    HANDLED_TYPES = {"kf_msg_or_event"}
    DEFAULT_WELCOME_REPLY = "您好！我是群码自助机器人，请把订单号发给我获取二维码"
    WELCOME_CACHE_TTL_SECONDS = 60

    def __init__(self):
        # 简单进程内锁，生产建议换成 Redis 分布式锁防止多实例并发拉取。
        self._lock = threading.Lock()
        self._pulling = set()
        self._session_api = KfSessionApi()
        self._staff_api = KfStaffApi()
        self._contact_way_api = ContactWayApi()
        self._cursor_store = KfCursorStore()
        self._sender = KfMessageSender(self._session_api)
        self._config_cache = KfConfigCache(
            self.WELCOME_CACHE_TTL_SECONDS, self.DEFAULT_WELCOME_REPLY
        )
        self._order_processor = KfOrderProcessor(
            self._contact_way_api, self._sender, self._config_cache
        )

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

        access_token = token_service.get_corp_access_token(corp_id or config.WXWORK_CORP_ID)
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
            cursor = self._cursor_store.load(open_kfid)
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
                self._cursor_store.save(open_kfid, next_cursor, corp_id)

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
            self._handle_event(raw, payload, access_token, corp_id)
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

        menu_id = None
        if payload and isinstance(payload, dict):
            menu_id = payload.get("menu_id")
        elif isinstance(msg.get("text"), dict):
            menu_id = msg.get("text", {}).get("menu_id")
        if menu_id:
            reply = self._config_cache.get_menu_reply(corp_id, open_kfid, str(menu_id))
            if reply:
                self._sender.send_reply_message(
                    access_token,
                    open_kfid,
                    external_userid,
                    reply,
                    msgid=msg.get("msgid"),
                    msgid_prefix="menu_",
                )
                if self._reply_contains_keyword(reply, "人工"):
                    self._transfer_to_servicer(access_token, open_kfid, external_userid, msg.get("msgid"))
            else:
                print("[biz.kf] menu_id has no reply configured", menu_id, flush=True)
            return

        if not is_order_no:
            if "人工" in content:
                self._transfer_to_servicer(access_token, open_kfid, external_userid, msg.get("msgid"))
                return
            self._sender.send_text_reply(
                access_token,
                open_kfid,
                external_userid,
                "查询失败，请输入有效的订单号重新获取",
                msgid=msg.get("msgid"),
                msgid_prefix="invalid_",
            )
            time.sleep(0.5)
            config = self._config_cache.get_config(corp_id, open_kfid)
            if config and config.get("msgtype") == "msgmenu":
                payload = config.get("payload")
                if isinstance(payload, dict):
                    menu_payload = dict(payload)
                    menu_payload["head_content"] = "如需其他服务，请点击"
                    self._sender.send_reply_message(
                        access_token,
                        open_kfid,
                        external_userid,
                        ("msgmenu", menu_payload),
                        msgid=msg.get("msgid"),
                        msgid_prefix="menu_hint_invalid_",
                    )
            return

        self._order_processor.handle_order(
            access_token,
            corp_id,
            open_kfid,
            external_userid,
            order_no,
            msgid=str(msg.get("msgid") or ""),
        )

    def _handle_event(self, msg: Dict, payload: Optional[Dict[str, Any]], access_token: str, corp_id: str) -> None:
        event_payload = payload if isinstance(payload, dict) else (msg.get("event") or {})
        event = event_payload.get("event_type")
        if event == "enter_session":
            self._on_enter_session(msg, event_payload, access_token, corp_id)
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
    def _on_enter_session(self, msg: Dict, payload: Dict, access_token: str, corp_id: str) -> None:
        welcome_code = payload.get("welcome_code")
        if not welcome_code:
            print("[biz.kf] enter_session missing welcome_code", msg.get("msgid"), flush=True)
            return

        open_kfid = msg.get("open_kfid")
        msgtype, body = self._config_cache.get_welcome_message(corp_id, open_kfid)
        payload = {"code": welcome_code, "msgtype": msgtype, msgtype: body}
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

    def _transfer_to_servicer(
        self, access_token: str, open_kfid: str, external_userid: str, msgid: Optional[str]
    ) -> None:
        try:
            data = self._staff_api.list_staffs(access_token, open_kfid)
        except Exception as exc:
            print("[biz.kf] list_staffs failed", msgid, "err=", exc, flush=True)
            return

        servicers = data.get("servicer_list") if isinstance(data, dict) else None
        if not isinstance(servicers, list):
            print("[biz.kf] servicer_list invalid", msgid, flush=True)
            return

        target_userid = None
        for item in servicers:
            if not isinstance(item, dict):
                continue
            userid = item.get("userid")
            status = item.get("status")
            if userid and status == 0:
                target_userid = userid
                break

        if not target_userid:
            print("[biz.kf] no available servicer", msgid, flush=True)
            return

        try:
            self._session_api.trans_service_state(
                access_token,
                open_kfid,
                external_userid,
                3,
                servicer_userid=target_userid,
            )
        except Exception as exc:
            print("[biz.kf] trans_service_state failed", msgid, "err=", exc, flush=True)

    @staticmethod
    def _reply_contains_keyword(reply: Tuple[str, Dict[str, Any]], keyword: str) -> bool:
        msgtype, body = reply
        if not keyword:
            return False

        def _scan(value) -> bool:
            if isinstance(value, str):
                return keyword in value
            if isinstance(value, dict):
                return any(_scan(v) for v in value.values())
            if isinstance(value, list):
                return any(_scan(v) for v in value)
            return False

        return _scan({"msgtype": msgtype, "body": body})
