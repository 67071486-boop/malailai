"""企业微信「客户联系」回调业务处理：支持 change_external_chat create/update/dismiss。"""
from datetime import datetime
from typing import Dict, Optional

from ..dispatcher import BizHandler
from wxcloudrun.services.wecom.externalcontact.group_chat_manager import ContactGroupChatApi
from wxcloudrun.services import token_service
from wxcloudrun.dao import query_corp_auth, upsert_group_chat, mark_group_chat_dismissed


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

        if change_type == "create":
            self._handle_chat_create(access_token, chat_id, corp_id)
        elif change_type == "update":
            self._handle_chat_update(access_token, chat_id, corp_id, xml)
        elif change_type == "dismiss":
            self._handle_chat_dismiss(chat_id)
        else:
            print("[biz.contact] unsupported ChangeType", change_type, flush=True)

    def _handle_chat_create(self, access_token: str, chat_id: str, corp_id: str):
        try:
            data = self.group_api.get_group_chat(access_token, chat_id)
            gc = data.get("group_chat", {}) if isinstance(data, dict) else {}
            if not gc:
                print("[biz.contact] empty group_chat for", chat_id, flush=True)
                return
            # 清理冗余字段
            gc.pop("notice", None)
            gc.pop("member_list", None)
            gc["corp_id"] = corp_id
            gc["status_code"] = gc.get("status", 0)  # 0 正常
            gc["status_text"] = "active"
            gc.setdefault("created_at", datetime.utcnow())
            gc["updated_at"] = datetime.utcnow()
            upsert_group_chat(gc)
            print("[biz.contact] group_chat created", chat_id, flush=True)
        except Exception as exc:
            print("[biz.contact] create handler error", chat_id, exc, flush=True)

    def _handle_chat_update(self, access_token: str, chat_id: str, corp_id: str, xml: Dict):
        update_detail = xml.get("UpdateDetail")
        if update_detail == "change_name":
            new_name = xml.get("Name") or xml.get("ChatName")
            if not new_name:
                print("[biz.contact] change_name missing Name", chat_id, flush=True)
                return
            doc = {
                "chat_id": chat_id,
                "corp_id": corp_id,
                "name": new_name,
                "updated_at": datetime.utcnow(),
            }
            upsert_group_chat(doc)
            print("[biz.contact] group_chat name updated", chat_id, flush=True)
            return

        # 对其他变更场景：可补充更多逻辑，先刷新基础信息
        try:
            data = self.group_api.get_group_chat(access_token, chat_id)
            gc = data.get("group_chat", {}) if isinstance(data, dict) else {}
            if not gc:
                print("[biz.contact] update fetch empty", chat_id, flush=True)
                return
            gc.pop("notice", None)
            gc.pop("member_list", None)
            gc["corp_id"] = corp_id
            gc["status_code"] = gc.get("status", 0)
            gc["status_text"] = "active"
            gc["updated_at"] = datetime.utcnow()
            upsert_group_chat(gc)
            print("[biz.contact] group_chat updated detail", update_detail, chat_id, flush=True)
        except Exception as exc:
            print("[biz.contact] update handler error", chat_id, exc, flush=True)

    def _handle_chat_dismiss(self, chat_id: str):
        try:
            mark_group_chat_dismissed(chat_id)
            print("[biz.contact] group_chat dismissed", chat_id, flush=True)
        except Exception as exc:
            print("[biz.contact] dismiss handler error", chat_id, exc, flush=True)
