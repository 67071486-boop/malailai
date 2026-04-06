import hashlib
from typing import Any, Dict, Optional, Tuple


class KfMessageSender:
    def __init__(self, session_api) -> None:
        self._session_api = session_api

    def send_text_reply(
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
        self._attach_msgid(payload, msgid, msgid_prefix)

        try:
            self._session_api.send_message(access_token, payload)
        except Exception as exc:
            print("[biz.kf] send_message failed", msgid, "err=", exc, flush=True)

    def send_reply_message(
        self,
        access_token: str,
        open_kfid: str,
        external_userid: str,
        reply: Tuple[str, Dict[str, Any]],
        *,
        msgid: Optional[str] = None,
        msgid_prefix: str = "",
    ) -> None:
        msgtype, body = reply
        payload = {
            "touser": external_userid,
            "open_kfid": open_kfid,
            "msgtype": msgtype,
            msgtype: body,
        }
        self._attach_msgid(payload, msgid, msgid_prefix)
        try:
            self._session_api.send_message(access_token, payload)
        except Exception as exc:
            print("[biz.kf] send_message failed", msgid, "err=", exc, flush=True)

    @staticmethod
    def _attach_msgid(payload: Dict[str, Any], msgid: Optional[str], msgid_prefix: str) -> None:
        if not msgid:
            return
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
