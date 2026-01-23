import json
import re
import xmltodict
from flask import jsonify
from wxcloudrun.wechat_official.WXBizMsgCrypt import WXBizMsgCrypt

from wxcloudrun.services.token_service import (
    WXWORK_CORP_ID,
    WXWORK_SUITE_ID,
    WXWORK_TOKEN,
    WXWORK_ENCODING_AES_KEY,
    save_suite_ticket,
    get_suite_access_token,
)
from wxcloudrun.services.auth_service import async_get_permanent_code


def _validate_params(params, required):
    missing = [p for p in required if p not in params or not params[p]]
    if missing:
        print("[callback_service] Missing parameters:", ", ".join(missing), "args=", dict(params))
        return False, f"Missing parameters: {', '.join(missing)}"
    return True, ""


def _verify_url(args, receive_id):
    wxcpt = WXBizMsgCrypt(WXWORK_TOKEN, WXWORK_ENCODING_AES_KEY, receive_id)
    valid, error = _validate_params(args, ["msg_signature", "timestamp", "nonce", "echostr"])
    if not valid:
        return error, 400

    msg_signature = args.get("msg_signature")
    timestamp = args.get("timestamp")
    nonce = args.get("nonce")
    echostr = args.get("echostr")
    ret, sEchoStr = wxcpt.VerifyURL(msg_signature, timestamp, nonce, echostr)
    if ret == 0:
        return sEchoStr, 200
    return "VerifyURL failed", 400


def _decrypt_body(body: str, msg_signature: str, timestamp: str, nonce: str, receive_id: str):
    wxcpt = WXBizMsgCrypt(WXWORK_TOKEN, WXWORK_ENCODING_AES_KEY, receive_id)
    try:
        ret, decrypted_xml = wxcpt.DecryptMsg(body, msg_signature, timestamp, nonce)
        if ret != 0:
            print(
                "[callback_service] DecryptMsg failed ret=", ret,
                "msg_signature=", msg_signature,
                "receive_id=", receive_id,
            )
            return None
        decrypted_dict = xmltodict.parse(decrypted_xml)
        return json.loads(json.dumps(decrypted_dict))
    except Exception as e:
        print("[callback_service] Decrypt or parse exception:", e)
        return None


def handle_data_callback(request):
    if request.method == "GET":
        return _verify_url(request.args, WXWORK_CORP_ID)

    if request.method == "POST":
        valid, error = _validate_params(request.args, ["msg_signature", "timestamp", "nonce"])
        if not valid:
            return jsonify({"code": 1, "message": error}), 400

        msg_signature = request.args.get("msg_signature")
        timestamp = request.args.get("timestamp")
        nonce = request.args.get("nonce")
        post_data = request.data.decode("utf-8")

        m = re.search(r"<ToUserName><!\[CDATA\[(.*?)\]\]></ToUserName>", post_data)
        receive_id = m.group(1) if m else WXWORK_SUITE_ID
        decrypted_json = _decrypt_body(post_data, msg_signature, timestamp, nonce, receive_id)
        if decrypted_json is None:
            print(
                "[callback_service] Failed to decrypt data callback. args=",
                dict(request.args), "body=", post_data[:1000]
            )
            return jsonify({"code": 1, "message": "DecryptMsg fail"}), 400

        # 这里可以扩展数据事件处理逻辑
        print("[callback_service] data callback decrypted receive_id=", receive_id)
        return "success", 200

    return "Method Not Allowed", 405


def handle_command_callback(request):
    if request.method == "GET":
        return _verify_url(request.args, WXWORK_CORP_ID)

    if request.method == "POST":
        valid, error = _validate_params(request.args, ["msg_signature", "timestamp", "nonce"])
        if not valid:
            return jsonify({"code": 1, "message": error}), 400

        msg_signature = request.args.get("msg_signature")
        timestamp = request.args.get("timestamp")
        nonce = request.args.get("nonce")
        post_data = request.data.decode("utf-8")

        m = re.search(r"<ToUserName><!\[CDATA\[(.*?)\]\]></ToUserName>", post_data)
        receive_id = m.group(1) if m else WXWORK_SUITE_ID
        decrypted_json = _decrypt_body(post_data, msg_signature, timestamp, nonce, receive_id)
        if decrypted_json is None:
            print(
                "[callback_service] Failed to decrypt command callback. args=",
                dict(request.args), "body=", post_data[:1000]
            )
            return jsonify({"code": 1, "message": "DecryptMsg fail"}), 400

        info_type = decrypted_json.get("xml", {}).get("InfoType")
        print("[callback_service] command callback InfoType=", info_type, "receive_id=", receive_id)
        if info_type == "suite_ticket":
            suite_ticket = decrypted_json.get("xml", {}).get("SuiteTicket")
            if suite_ticket:
                try:
                    save_suite_ticket(suite_ticket)
                    print("[callback_service] saved suite_ticket length=", len(suite_ticket))
                    get_suite_access_token()
                except Exception:
                    import traceback

                    print("[callback_service] Exception handling suite_ticket")
                    traceback.print_exc()
        elif info_type == "create_auth":
            auth_code = decrypted_json.get("xml", {}).get("AuthCode")
            if auth_code:
                try:
                    print("[callback_service] received AuthCode=", auth_code)
                    async_get_permanent_code(auth_code)
                except Exception:
                    import traceback

                    print("[callback_service] Exception starting async get_permanent_code for auth_code=", auth_code)
                    traceback.print_exc()
        # 可扩展更多 InfoType 分支
        return "success", 200

    return "Method Not Allowed", 405


__all__ = ["handle_data_callback", "handle_command_callback"]
