import time
import logging
import requests
from flask import Blueprint, request, jsonify
from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
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

@wxwork_bp.route('/get_suite_token', methods=['GET'])
def get_suite_token():
    """获取 Suite Access Token API"""
    try:
        token = get_suite_access_token()
        if token:
            return jsonify({'code': 0, 'suite_access_token': token})
        else:
            return jsonify({'code': 1, 'message': '获取失败'})
    except Exception as e:
        logger.error(f"获取 Suite Token API 异常: {e}")
        return jsonify({'code': 1, 'message': '服务器内部错误'})
def callback():
    """企业微信回调处理"""
    try:
        crypto = WeChatCrypto(WXWORK_TOKEN, WXWORK_ENCODING_AES_KEY, WXWORK_CORP_ID)

        if request.method == 'GET':
            # GET 请求：验证回调 URL
            msg_signature = request.args.get('msg_signature')
            timestamp = request.args.get('timestamp')
            nonce = request.args.get('nonce')
            echostr = request.args.get('echostr')

            if not all([msg_signature, timestamp, nonce, echostr]):
                return 'Invalid parameters', 400

            try:
                decrypted_echostr = crypto.check_signature(msg_signature, timestamp, nonce, echostr)
                return decrypted_echostr
            except InvalidSignatureException:
                return 'Invalid signature', 400

        elif request.method == 'POST':
            # POST 请求：处理回调消息
            msg_signature = request.args.get('msg_signature')
            timestamp = request.args.get('timestamp')
            nonce = request.args.get('nonce')

            if not all([msg_signature, timestamp, nonce]):
                return jsonify({'code': 1, 'message': 'Invalid parameters'}), 400

            # 获取加密消息
            encrypted_xml = request.data.decode('utf-8')

            try:
                # 解密消息
                decrypted_xml = crypto.decrypt_message(encrypted_xml, msg_signature, timestamp, nonce)
                logger.info(f"解密后的消息: {decrypted_xml}")

                # 解析 XML 为 dict
                import xml.etree.ElementTree as ET
                root = ET.fromstring(decrypted_xml)
                info_type = root.find('InfoType').text if root.find('InfoType') is not None else None

                if info_type == 'suite_ticket':
                    suite_ticket = root.find('SuiteTicket').text
                    global _suite_ticket
                    _suite_ticket = suite_ticket
                    logger.info(f"收到 Suite Ticket: {suite_ticket}")
                else:
                    logger.info(f"收到其他回调类型: {info_type}")

                # TODO: 处理其他业务逻辑

                # 响应 success
                return 'success'

            except InvalidSignatureException:
                return jsonify({'code': 1, 'message': 'Invalid signature'}), 400
            except Exception as e:
                logger.error(f"解密异常: {e}")
                return jsonify({'code': 1, 'message': 'Decrypt failed'}), 500

    except Exception as e:
        logger.error(f"回调处理异常: {e}")
        return jsonify({'code': 1, 'message': '处理失败'}), 500