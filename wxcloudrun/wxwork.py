import time
import logging
import requests
from flask import Blueprint, request, jsonify
from wxcloudrun.wechat_official.WXBizMsgCrypt import WXBizMsgCrypt
import os

# 企业微信配置（从环境变量读取）
WXWORK_CORP_ID = os.getenv("WXWORK_CORP_ID", "your_corp_id")
WXWORK_CORP_SECRET = os.getenv("WXWORK_CORP_SECRET", "your_corp_secret")
WXWORK_AGENT_ID = os.getenv("WXWORK_AGENT_ID", "your_agent_id")
WXWORK_TOKEN = os.getenv("WXWORK_TOKEN", "your_token")
WXWORK_ENCODING_AES_KEY = os.getenv("WXWORK_ENCODING_AES_KEY", "your_aes_key")
WXWORK_SUITE_ID = os.getenv("WXWORK_SUITE_ID", "your_suite_id")
WXWORK_SUITE_SECRET = os.getenv("WXWORK_SUITE_SECRET", "your_suite_secret")

# Access Token 缓存
_access_token = None
_token_expires = 0

# Suite Ticket 和 Suite Access Token 缓存
_suite_ticket = None
_suite_access_token = None
_suite_token_expires = 0

# 临时授权码缓存
_auth_code = None

wxwork_bp = Blueprint('wxwork', __name__, url_prefix='/wxwork')

logger = logging.getLogger(__name__)

def validate_base_params(params, required):
    """校验基础参数"""
    missing = [p for p in required if p not in params or not params[p]]
    if missing:
        return False, f"Missing parameters: {', '.join(missing)}"
    return True, ""

def validate_signature(crypto, signature, timestamp, nonce, data):
    """校验签名"""
    try:
        crypto.check_signature(signature, timestamp, nonce, data)
        return True, ""
    except InvalidSignatureException:
        return False, "Invalid signature"

def get_access_token():
    """获取企业微信 Access Token（带缓存）"""
    global _access_token, _token_expires

    current_time = time.time()
    if _access_token and current_time < _token_expires:
        return _access_token

    try:
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={WXWORK_CORP_ID}&corpsecret={WXWORK_CORP_SECRET}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('errcode') == 0:
            _access_token = data['access_token']
            # Token 有效期7200秒，提前5分钟过期
            _token_expires = current_time + 7200 - 300
            logger.info("成功获取企业微信 Access Token")
            return _access_token
        else:
            logger.error(f"获取 Access Token 失败: {data}")
            return None
    except Exception as e:
        logger.error(f"获取 Access Token 异常: {e}")
        return None

def get_suite_access_token():
    """获取第三方应用 Suite Access Token（带缓存）"""
    global _suite_access_token, _suite_token_expires, _suite_ticket

    current_time = time.time()
    if _suite_access_token and current_time < _suite_token_expires:
        return _suite_access_token

    if not _suite_ticket:
        logger.error("Suite Ticket 为空，无法获取 Suite Access Token")
        return None

    try:
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_suite_token"
        data = {
            "suite_id": WXWORK_SUITE_ID,
            "suite_secret": WXWORK_SUITE_SECRET,
            "suite_ticket": _suite_ticket
        }
        response = requests.post(url, json=data, timeout=10)
        result = response.json()

        if result.get('errcode') == 0:
            _suite_access_token = result['suite_access_token']
            # Token 有效期7200秒，提前5分钟过期
            _suite_token_expires = current_time + 7200 - 300
            logger.info("成功获取 Suite Access Token")
            return _suite_access_token
        else:
            logger.error(f"获取 Suite Access Token 失败: {result}")
            return None
    except Exception as e:
        logger.error(f"获取 Suite Access Token 异常: {e}")
        return None


def get_permanent_code(auth_code):
    """获取企业永久授权码"""
    suite_token = get_suite_access_token()
    if not suite_token:
        logger.error("获取 Suite Access Token 失败")
        return None

    try:
        url = f"https://qyapi.weixin.qq.com/cgi-bin/service/get_permanent_code?suite_access_token={suite_token}"
        data = {"auth_code": auth_code}
        response = requests.post(url, json=data, timeout=10)
        result = response.json()

        if result.get('errcode') == 0:
            permanent_code = result['permanent_code']
            auth_corp_info = result.get('auth_corp_info', {})
            corp_id = auth_corp_info.get('corpid')

            # 保存到数据库
            from wxcloudrun.dao import query_corp_auth, insert_corp_auth, update_corp_auth
            from wxcloudrun.model import CorpAuth
            import json

            corp_auth = query_corp_auth(corp_id)
            if corp_auth:
                corp_auth.permanent_code = permanent_code
                corp_auth.auth_corp_info = json.dumps(auth_corp_info)
                update_corp_auth(corp_auth)
            else:
                corp_auth = CorpAuth(
                    corp_id=corp_id,
                    permanent_code=permanent_code,
                    auth_corp_info=json.dumps(auth_corp_info)
                )
                insert_corp_auth(corp_auth)

            logger.info(f"获取永久授权码成功: {corp_id}")
            return permanent_code, auth_corp_info
        else:
            logger.error(f"获取永久授权码失败: {result}")
            return None
    except Exception as e:
        logger.error(f"获取永久授权码异常: {e}")
        return None


def send_text_message(user_id, content):
    """发送文本消息"""
    access_token = get_access_token()
    if not access_token:
        return False, "获取 Access Token 失败"

    try:
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
        data = {
            "touser": user_id,
            "msgtype": "text",
            "agentid": WXWORK_AGENT_ID,
            "text": {
                "content": content
            }
        }

        response = requests.post(url, json=data, timeout=10)
        result = response.json()

        if result.get('errcode') == 0:
            logger.info(f"消息发送成功: {user_id}")
            return True, "发送成功"
        else:
            logger.error(f"消息发送失败: {result}")
            return False, result.get('errmsg', '发送失败')
    except Exception as e:
        logger.error(f"发送消息异常: {e}")
        return False, str(e)

@wxwork_bp.route('/send_message', methods=['POST'])
def send_message():
    """发送企业微信消息 API"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        content = data.get('content')

        if not user_id or not content:
            return jsonify({'code': 1, 'message': '缺少 user_id 或 content 参数'})

        success, message = send_text_message(user_id, content)

        if success:
            return jsonify({'code': 0, 'message': message})
        else:
            return jsonify({'code': 1, 'message': message})

    except Exception as e:
        logger.error(f"发送消息API异常: {e}")
        return jsonify({'code': 1, 'message': '服务器内部错误'})

@wxwork_bp.route('/get_permanent_code', methods=['POST'])
def get_permanent_code_api():
    """获取永久授权码 API"""
    try:
        data = request.get_json()
        auth_code = data.get('auth_code') or _auth_code

        if not auth_code:
            return jsonify({'code': 1, 'message': '缺少 auth_code 参数，且缓存中无临时授权码'})

        result = get_permanent_code(auth_code)
        if result:
            permanent_code, auth_corp_info = result
            return jsonify({'code': 0, 'permanent_code': permanent_code, 'auth_corp_info': auth_corp_info})
        else:
            return jsonify({'code': 1, 'message': '获取永久授权码失败'})
    except Exception as e:
        logger.error(f"获取永久授权码API异常: {e}")
        return jsonify({'code': 1, 'message': '服务器内部错误'})
@wxwork_bp.route('/callback', methods=['GET', 'POST'])
def callback():
    """企业微信回调处理"""
    try:
        try:
            wxcpt = WXBizMsgCrypt(WXWORK_TOKEN, WXWORK_ENCODING_AES_KEY, WXWORK_CORP_ID)
        except Exception as e:
            logger.error(f"WXBizMsgCrypt初始化失败: {e}")
            return 'Crypto init failed', 500

        if request.method == 'GET':
            # GET 请求：验证回调 URL
            valid, error = validate_base_params(request.args, ['msg_signature', 'timestamp', 'nonce', 'echostr'])
            if not valid:
                return error, 400

            msg_signature = request.args.get('msg_signature')
            timestamp = request.args.get('timestamp')
            nonce = request.args.get('nonce')
            echostr = request.args.get('echostr')

            try:
                ret, sEchoStr = wxcpt.VerifyURL(msg_signature, timestamp, nonce, echostr)
                if ret == 0:
                    logger.info(f"验证URL成功: {sEchoStr}")
                    return sEchoStr
                else:
                    logger.error(f"VerifyURL失败: {ret}")
                    return 'VerifyURL fail', 400
            except Exception as e:
                logger.error(f"GET验证异常: {e}")
                return 'Verify failed', 500

        elif request.method == 'POST':
            # POST 请求：处理回调消息
            valid, error = validate_base_params(request.args, ['msg_signature', 'timestamp', 'nonce'])
            if not valid:
                return jsonify({'code': 1, 'message': error}), 400

            msg_signature = request.args.get('msg_signature')
            timestamp = request.args.get('timestamp')
            nonce = request.args.get('nonce')

            # 获取加密消息
            encrypted_xml = request.data.decode('utf-8')

            try:
                ret, sMsg = wxcpt.DecryptMsg(encrypted_xml, msg_signature, timestamp, nonce)
                if ret != 0:
                    logger.error(f"DecryptMsg失败: {ret}")
                    return jsonify({'code': 1, 'message': 'DecryptMsg fail'}), 400

                decrypted_xml = sMsg
                logger.info(f"解密后的消息: {decrypted_xml}")

                # 检查是否为有效XML
                if not decrypted_xml.startswith('<'):
                    logger.error(f"解密结果不是XML格式: {decrypted_xml}")
                    return jsonify({'code': 1, 'message': 'Invalid decrypted content'}), 400

                # 解析 XML 为 dict
                import xml.etree.ElementTree as ET
                root = ET.fromstring(decrypted_xml)
                info_type = root.find('InfoType').text if root.find('InfoType') is not None else None

                if info_type == 'suite_ticket':
                    suite_ticket = root.find('SuiteTicket').text
                    global _suite_ticket
                    _suite_ticket = suite_ticket
                    logger.info(f"收到 Suite Ticket: {suite_ticket}")
                elif info_type == 'create_auth':
                    auth_code = root.find('AuthCode').text
                    global _auth_code
                    _auth_code = auth_code
                    logger.info(f"收到临时授权码: {auth_code}")
                    # 立即获取永久授权码
                    permanent_result = get_permanent_code(auth_code)
                    if permanent_result:
                        logger.info("永久授权码获取成功")
                    else:
                        logger.error("永久授权码获取失败")
                else:
                    logger.info(f"收到其他回调类型: {info_type}")

                # TODO: 处理其他业务逻辑

                # 响应 success
                return 'success'

            except ET.ParseError as e:
                logger.error(f"XML解析异常: {e}, 内容: {decrypted_xml}")
                return jsonify({'code': 1, 'message': 'XML parse failed'}), 500
            except Exception as e:
                logger.error(f"解密异常: {e}")
                return jsonify({'code': 1, 'message': 'Decrypt failed'}), 500

    except Exception as e:
        logger.error(f"回调处理异常: {e}")
        return jsonify({'code': 1, 'message': '处理失败'}), 500