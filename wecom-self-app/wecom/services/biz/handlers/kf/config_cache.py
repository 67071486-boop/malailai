import threading
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Tuple

from wecom.dao import query_kf_welcome


class KfConfigCache:
    def __init__(self, ttl_seconds: int, default_welcome: str) -> None:
        self._ttl_seconds = ttl_seconds
        self._default_welcome = default_welcome
        self._config_lock = threading.Lock()
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._welcome_lock = threading.Lock()
        self._welcome_cache: Dict[str, Dict[str, Any]] = {}

    def get_config(self, corp_id: str, open_kfid: Optional[str]) -> Optional[Dict[str, Any]]:
        key = f"{corp_id}:{open_kfid or ''}"
        now = datetime.now(timezone.utc)
        with self._config_lock:
            cached = self._config_cache.get(key)
            if cached and cached.get("expires_at") and cached["expires_at"] > now:
                return cached["value"]

        doc = query_kf_welcome(corp_id, open_kfid)
        if not doc and open_kfid:
            doc = query_kf_welcome(corp_id, None)

        with self._config_lock:
            self._config_cache[key] = {
                "value": doc,
                "expires_at": now + timedelta(seconds=self._ttl_seconds),
            }
        return doc

    def get_welcome_message(self, corp_id: str, open_kfid: Optional[str]) -> Tuple[str, Dict[str, Any]]:
        key = f"{corp_id}:{open_kfid or ''}"
        now = datetime.now(timezone.utc)
        with self._welcome_lock:
            cached = self._welcome_cache.get(key)
            if cached and cached.get("expires_at") and cached["expires_at"] > now:
                return cached["value"]

        doc = self.get_config(corp_id, open_kfid)

        msgtype = "text"
        body: Dict[str, Any] = {"content": self._default_welcome}
        if doc:
            stored_type = doc.get("msgtype")
            stored_payload = doc.get("payload")
            if isinstance(stored_type, str) and isinstance(stored_payload, dict):
                msgtype = stored_type
                body = stored_payload
            else:
                legacy = doc.get("welcome_reply")
                if isinstance(legacy, str) and legacy.strip():
                    body = {"content": legacy}

        with self._welcome_lock:
            self._welcome_cache[key] = {
                "value": (msgtype, body),
                "expires_at": now + timedelta(seconds=self._ttl_seconds),
            }
        return msgtype, body

    def get_menu_reply(
        self, corp_id: str, open_kfid: Optional[str], menu_id: str
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        doc = self.get_config(corp_id, open_kfid)
        if not doc or not menu_id:
            return None

        menu_replies = doc.get("menu_replies")
        if isinstance(menu_replies, dict) and menu_id in menu_replies:
            reply = menu_replies.get(menu_id)
            normalized = self._normalize_reply(reply)
            if normalized:
                return normalized
        return None

    @staticmethod
    def _normalize_reply(reply: Any) -> Optional[Tuple[str, Dict[str, Any]]]:
        if not isinstance(reply, dict):
            return None
        msgtype = reply.get("msgtype")
        if not isinstance(msgtype, str) or not msgtype.strip():
            return None
        msgtype = msgtype.strip()
        body = None
        if msgtype in reply and isinstance(reply.get(msgtype), dict):
            body = reply.get(msgtype)
        elif isinstance(reply.get("payload"), dict):
            body = reply.get("payload")
        if not isinstance(body, dict):
            return None
        return msgtype, body
