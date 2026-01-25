"""企业微信「客户联系」回调业务处理：支持 change_external_chat create/update/dismiss。"""
from datetime import datetime, timezone
from typing import Dict, Optional

from ..dispatcher import BizHandler
from wxcloudrun.services.wecom.externalcontact.group_chat_manager import ContactGroupChatApi
from wxcloudrun.services import token_service
from wxcloudrun.dao import query_corp_auth, query_group_chat, upsert_group_chat, mark_group_chat_dismissed


class ContactEventHandler(BizHandler):
    HANDLED_TYPES = {"change_external_chat"}

    def __init__(self):
        self.group_api = ContactGroupChatApi()

    def can_handle(self, info_type: Optional[str], payload: Dict) -> bool:
        return info_type in self.HANDLED_TYPES

    def handle(self, info_type: Optional[str], payload: Dict, *, receive_id: Optional[str], source: str) -> None:
        xml = payload.get("xml", {}) if isinstance(payload, dict) else {}
        change_type = xml.get("ChangeType")
        chat_id = xml.get("ChatId")
        corp_id = xml.get("AuthCorpId") or xml.get("ToUserName")

        if not corp_id or not chat_id:
            print("[biz.contact] missing corp_id or chat_id", xml, flush=True)
            return

        corp_auth = query_corp_auth(corp_id)
        if not corp_auth or not corp_auth.get("permanent_code"):
            print("[biz.contact] corp_auth not found for", corp_id, flush=True)
            return

        access_token = token_service.get_corp_access_token(corp_id, corp_auth["permanent_code"])
        if not access_token:
            print("[biz.contact] access_token unavailable for", corp_id, flush=True)
            return

        update_detail = xml.get("UpdateDetail")

        if change_type == "create":
            self._sync_group_chat(access_token, chat_id, corp_id, update_detail=update_detail)
        elif change_type == "update":
            if update_detail == "change_name":
                self._sync_group_chat(access_token, chat_id, corp_id, update_detail=update_detail)
            else:
                print("[biz.contact] update ignored, unsupported detail", update_detail, chat_id, flush=True)
        elif change_type == "dismiss":
            self._handle_chat_dismiss(chat_id)
        else:
            print("[biz.contact] unsupported ChangeType", change_type, flush=True)

    def _sync_group_chat(self, access_token: str, chat_id: str, corp_id: str, update_detail: Optional[str] = None):
        """从企微拉取客户群详情并写入数据库，若不存在则新增。"""
        try:
            data = self.group_api.get_group_chat(access_token, chat_id)
            gc = data.get("group_chat", {}) if isinstance(data, dict) else {}
            if not gc:
                print("[biz.contact] fetch group_chat empty", chat_id, flush=True)
                return
            gc.pop("notice", None)
            gc.pop("member_list", None)
            gc["corp_id"] = corp_id
            gc["status_code"] = gc.get("status", 0)
            gc["status_text"] = "active"
            existing = query_group_chat(chat_id)
            if existing and existing.get("created_at"):
                gc.setdefault("created_at", existing.get("created_at"))
            else:
                gc.setdefault("created_at", datetime.now(timezone.utc))
            gc["updated_at"] = datetime.now(timezone.utc)
            upsert_group_chat(gc)
            print("[biz.contact] group_chat synced", chat_id, "update_detail=", update_detail, flush=True)
        except Exception as exc:
            print("[biz.contact] sync handler error", chat_id, exc, flush=True)

    def _handle_chat_dismiss(self, chat_id: str):
        try:
            mark_group_chat_dismissed(chat_id)
            print("[biz.contact] group_chat dismissed", chat_id, flush=True)
        except Exception as exc:
            print("[biz.contact] dismiss handler error", chat_id, exc, flush=True)
