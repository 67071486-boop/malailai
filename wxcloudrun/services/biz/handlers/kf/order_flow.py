from datetime import datetime, timezone, timedelta
import time
import os
import tempfile
import requests
from typing import Optional

from wxcloudrun.dao import (
    query_group_chat_by_name,
    upsert_pending_order,
    mark_pending_done,
    upsert_group_chat,
)
from wxcloudrun.model import new_pending_order


class KfOrderProcessor:
    def __init__(self, contact_way_api, sender, config_cache) -> None:
        self._contact_way_api = contact_way_api
        self._sender = sender
        self._config_cache = config_cache

    def handle_order(
        self,
        access_token: str,
        corp_id: str,
        open_kfid: str,
        external_userid: str,
        order_no: str,
        *,
        msgid: str,
    ) -> None:
        group_chat = query_group_chat_by_name(corp_id, order_no)
        sent_qr = False
        reply_text = None
        if not group_chat:
            self._save_pending_order(corp_id, order_no, external_userid, open_kfid)
            reply_text = "订单对应的群正在创建中，创建完成后会自动推送二维码，请稍候"
        else:
            bound = group_chat.get("bound") if isinstance(group_chat.get("bound"), dict) else None
            bound_user = bound.get("external_userid") if bound else None
            if bound_user and bound_user != external_userid:
                reply_text = "该群已被其他用户获取，请联系人工服务"
                self._sender.send_text_reply(
                    access_token,
                    open_kfid,
                    external_userid,
                    reply_text,
                    msgid=msgid,
                    msgid_prefix="order_",
                )
                return

            chat_id = group_chat.get("chat_id")
            if not chat_id:
                reply_text = f"订单 {order_no} 对应群缺少 chat_id，无法生成二维码"
                self._sender.send_text_reply(
                    access_token,
                    open_kfid,
                    external_userid,
                    reply_text,
                    msgid=msgid,
                    msgid_prefix="order_",
                )
                return

            join_way = group_chat.get("join_way") if isinstance(group_chat.get("join_way"), dict) else None

            qr_code = join_way.get("qr_code") if isinstance(join_way, dict) else None
            if not qr_code:
                try:
                    payload = {
                        "scene": 2,
                        "remark": order_no,
                        "chat_id_list": [chat_id],
                    }
                    add_resp = self._contact_way_api.add_join_way(
                        access_token,
                        payload,
                        corp_id=corp_id,
                    )
                    join_way = add_resp.get("join_way") if isinstance(add_resp, dict) else None
                    qr_code = join_way.get("qr_code") if isinstance(join_way, dict) else None
                except Exception as exc:
                    print("[biz.kf] add_join_way failed", order_no, "err=", exc, flush=True)

            if qr_code and isinstance(join_way, dict):
                now = datetime.now(timezone.utc)
                media_id = join_way.get("media_id")
                expires_at = join_way.get("media_id_expires_at")
                expired = True
                if media_id and isinstance(expires_at, datetime):
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    expired = expires_at <= now
                if not media_id or expired:
                    media_id = self._fetch_media_id_from_qr(access_token, qr_code)
                    if media_id:
                        join_way["media_id"] = media_id
                        # 临时素材 3 天过期，预留 5 分钟缓冲
                        join_way["media_id_expires_at"] = now + timedelta(days=3) - timedelta(minutes=5)
                        group_chat["join_way"] = join_way

                if media_id:
                    self._sender.send_text_reply(
                        access_token,
                        open_kfid,
                        external_userid,
                        (
                            f"{order_no}群聊，老板扫二维码进群，等待我们安排打手\n"
                            "在上号之前请您先看一下本店的须知！！\n"
                            "①进群后我们会安排打手，只需等待打手即可\n"
                            "②订单的代练对接只会在群里，打手不会私下加您微信也不会私聊您\n"
                            "③如果打手私下主动加您找群主举报奖励现金50元！\n"
                            "④代练过程中如更换打手请您及时更改密码，删除登录ip地址\n"
                            "⑤订单完成后请您及时更改密码，删除登录ip地址，务必完成删号~"
                        ),
                        msgid=msgid,
                        msgid_prefix="order_txt_",
                    )
                    self._sender.send_reply_message(
                        access_token,
                        open_kfid,
                        external_userid,
                        ("image", {"media_id": media_id}),
                        msgid=msgid,
                        msgid_prefix="order_img_",
                    )
                    sent_qr = True
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
                else:
                    reply_text = f"订单 {order_no} 的入群二维码：{qr_code}"
            else:
                reply_text = f"订单 {order_no} 暂无法生成二维码，请稍后再试"

        if reply_text:
            self._sender.send_text_reply(
                access_token,
                open_kfid,
                external_userid,
                reply_text,
                msgid=msgid,
                msgid_prefix="order_",
            )

        if sent_qr:
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
                        msgid=msgid,
                        msgid_prefix="menu_hint_",
                    )

    @staticmethod
    def _save_pending_order(corp_id: str, order_no: str, external_userid: str, open_kfid: str) -> None:
        doc = new_pending_order(corp_id, order_no, external_userid, open_kfid)
        upsert_pending_order(doc)

    @staticmethod
    def _fetch_media_id_from_qr(access_token: str, qr_code: str) -> Optional[str]:
        if not qr_code:
            return None
        tmp_path = None
        try:
            resp = requests.get(qr_code, timeout=10)
            resp.raise_for_status()
            suffix = ".png"
            if "image/jpeg" in resp.headers.get("Content-Type", ""):
                suffix = ".jpg"
            fd, tmp_path = tempfile.mkstemp(prefix="kf_qr_", suffix=suffix)
            with os.fdopen(fd, "wb") as f:
                f.write(resp.content)
            from wxcloudrun.services.wecom.media_api import upload_temp_media

            data = upload_temp_media(access_token, "image", tmp_path)
            return data.get("media_id")
        except Exception as exc:
            print("[biz.kf] fetch media_id from qr failed", exc, flush=True)
            return None
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
