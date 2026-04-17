import json
import re
import xmltodict  # type: ignore
from flask import Request, jsonify
from flask.typing import ResponseReturnValue
from wecom.wechat_official.WXBizMsgCrypt import WXBizMsgCrypt

from wecom.services.service.token_service import (
    WXWORK_CORP_ID,
    WXWORK_TOKEN,
    WXWORK_ENCODING_AES_KEY,
)
from wecom.services.biz import biz_dispatcher


def _validate_params(params, required):
    missing = [p for p in required if p not in params or not params[p]]
    if missing:
        print("[callback_service] 缺少参数:", ", ".join(missing), "args=", dict(params), flush=True)
        return False, f"Missing parameters: {', '.join(missing)}"
    return True, ""


def _verify_url(args, receive_id) -> ResponseReturnValue:
    wxcpt = WXBizMsgCrypt(WXWORK_TOKEN, WXWORK_ENCODING_AES_KEY, receive_id)
    valid, error = _validate_params(args, ["msg_signature", "timestamp", "nonce", "echostr"])
    if not valid:
        return error, 400

    msg_signature = args.get("msg_signature")
    timestamp = args.get("timestamp")
    nonce = args.get("nonce")
    echostr = args.get("echostr")
    ret, sEchoStr = wxcpt.VerifyURL(msg_signature, timestamp, nonce, echostr)
    print("[callback_service] VerifyURL 返回:", ret, "sEchoStr=", sEchoStr, "receive_id=", receive_id, "args=", dict(args), flush=True)
    if ret == 0:
        return (sEchoStr or ""), 200
    return "VerifyURL failed", 400


def _decrypt_body(body: str, msg_signature: str, timestamp: str, nonce: str, receive_id: str):
    wxcpt = WXBizMsgCrypt(WXWORK_TOKEN, WXWORK_ENCODING_AES_KEY, receive_id)
    try:
        ret, decrypted_xml = wxcpt.DecryptMsg(body, msg_signature, timestamp, nonce)
        if ret != 0:
            print(
                "[callback_service] 解密失败 ret=", ret,
                "msg_signature=", msg_signature,
                "receive_id=", receive_id,
                flush=True,
            )
            return None

        if isinstance(decrypted_xml, bytes):
            decrypted_xml = decrypted_xml.decode("utf-8")
        if not isinstance(decrypted_xml, str):
            print(
                "[callback_service] 解密返回非字符串类型 ret=", ret,
                "type=", type(decrypted_xml),
                "receive_id=", receive_id,
                flush=True,
            )
            return None

        decrypted_dict = xmltodict.parse(decrypted_xml)
        return json.loads(json.dumps(decrypted_dict))
    except Exception as e:
        print("[callback_service] 解密或解析异常:", e, flush=True)
        return None


def _dispatch_biz(evt_type: str, payload: dict, *, receive_id: str, source: str):
    """将解密后的回调交给业务分发器，失败不影响回包。"""
    try:
        biz_dispatcher.dispatch(evt_type, payload, receive_id=receive_id, source=source)
    except Exception as exc:
        print("[callback_service] biz dispatch error", evt_type, "error=", exc, flush=True)


def _extract_event_type(decrypted_json: dict):
    """统一提取回调事件类型：优先 InfoType，其次 Event，再次 MsgType。"""
    xml = decrypted_json.get("xml", {}) if isinstance(decrypted_json, dict) else {}
    return xml.get("InfoType") or xml.get("Event") or xml.get("MsgType")


def _default_receive_id_from_body(post_data: str) -> str:
    m = re.search(r"<ToUserName><!\[CDATA\[(.*?)\]\]></ToUserName>", post_data)
    if m and m.group(1):
        return m.group(1)
    return WXWORK_CORP_ID or ""


def handle_wecom_callback(request: Request) -> ResponseReturnValue:
    """自建应用「接收消息」统一入口：URL 校验与消息/事件解密分发。"""
    if request.method == "GET":
        print("[callback_service] 收到 GET（URL 校验）", flush=True)
        return _verify_url(request.args, WXWORK_CORP_ID)

    if request.method == "POST":
        print("[callback_service] 收到 POST", flush=True)
        valid, error = _validate_params(request.args, ["msg_signature", "timestamp", "nonce"])
        if not valid:
            return jsonify({"code": 1, "message": error}), 400

        msg_signature = request.args["msg_signature"]
        timestamp = request.args["timestamp"]
        nonce = request.args["nonce"]
        post_data = request.data.decode("utf-8")

        receive_id = _default_receive_id_from_body(post_data)
        decrypted_json = _decrypt_body(post_data, msg_signature, timestamp, nonce, receive_id)
        if decrypted_json is None:
            print(
                "[callback_service] 解密失败 args=",
                dict(request.args), "body=", post_data[:1000],
                flush=True,
            )
            return jsonify({"code": 1, "message": "DecryptMsg fail"}), 400

        evt_type = _extract_event_type(decrypted_json)
        if not evt_type:
            print("[callback_service] 缺少事件类型，跳过分发 receive_id=", receive_id, flush=True)
            return "success", 200
        print("[callback_service] 解密成功 receive_id=", receive_id, "event=", evt_type, flush=True)
        _dispatch_biz(evt_type, decrypted_json, receive_id=receive_id, source="callback")
        return "success", 200

    return "Method Not Allowed", 405


def handle_data_callback(request: Request) -> ResponseReturnValue:
    """兼容旧路径 /callback/data，逻辑与统一入口一致。"""
    return handle_wecom_callback(request)


def handle_command_callback(request: Request) -> ResponseReturnValue:
    """兼容旧路径 /callback/command，逻辑与统一入口一致。"""
    return handle_wecom_callback(request)


__all__ = [
    "handle_wecom_callback",
    "handle_data_callback",
    "handle_command_callback",
]
