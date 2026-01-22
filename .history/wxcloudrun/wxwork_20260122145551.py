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


# Suite Ticket 和 Suite Access Token 缓存（建议用数据库或redis，示例用内存）
_suite_ticket = None
_suite_access_token = None
_suite_token_expires = 0

def save_suite_ticket(ticket):
    global _suite_ticket
    _suite_ticket = ticket
    print(f"[缓存] suite_ticket 已保存: {_suite_ticket}")

def get_suite_ticket():
    return _suite_ticket

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
        print(f"[缓存] suite_access_token 命中: {_suite_access_token}")
        return _suite_access_token

    suite_ticket = get_suite_ticket()
    if not suite_ticket:
        print("[错误] Suite Ticket 为空，无法获取 Suite Access Token")
        return None

    try:
        url = "https://qyapi.weixin.qq.com/cgi-bin/service/get_suite_token"
        data = {
            "suite_id": WXWORK_SUITE_ID,
            "suite_secret": WXWORK_SUITE_SECRET,
            "suite_ticket": suite_ticket
        }
        print(f"[请求] 获取 suite_access_token: {data}")
        response = requests.post(url, json=data, timeout=10)
        result = response.json()

        if result.get('errcode') == 0:
            _suite_access_token = result['suite_access_token']
            # Token 有效期7200秒，提前5分钟过期
            _suite_token_expires = current_time + 7200 - 300
            print(f"[成功] 获取 suite_access_token: {_suite_access_token}")
            return _suite_access_token
        else:
            print(f"[失败] 获取 suite_access_token: {result}")
            return None
    except Exception as e:
        print(f"[异常] 获取 suite_access_token: {e}")
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
            from wxcloudrun.model import new_corp_auth
            import json

            corp_auth = query_corp_auth(corp_id)
            if corp_auth:
                corp_auth['permanent_code'] = permanent_code
                corp_auth['auth_corp_info'] = json.dumps(auth_corp_info)
                update_corp_auth(corp_auth)
            else:
                corp_auth = new_corp_auth(
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
        wxcpt = WXBizMsgCrypt(WXWORK_TOKEN, WXWORK_ENCODING_AES_KEY, WXWORK_CORP_ID)
        print("[WXBizMsgCrypt] 初始化成功")
    except Exception as e:
        print(f"[WXBizMsgCrypt] 初始化失败: {e}")
        return 'Crypto init failed', 500

    if request.method == 'GET':
        print("[回调验证] 收到 GET 请求，参数:", dict(request.args))
        valid, error = validate_base_params(request.args, ['msg_signature', 'timestamp', 'nonce', 'echostr'])
        if not valid:
            print(f"[回调验证] 参数校验失败: {error}")
            return error, 400

        msg_signature = request.args.get('msg_signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        echostr = request.args.get('echostr')

        print(f"[回调验证] msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}, echostr={echostr}")
        try:
            ret, sEchoStr = wxcpt.VerifyURL(msg_signature, timestamp, nonce, echostr)
            print(f"[回调验证] VerifyURL 返回: ret={ret}, sEchoStr={sEchoStr}")
            if ret == 0:
                print(f"验证URL成功: {sEchoStr}")
                return sEchoStr
            else:
                print(f"验证URL失败: ret={ret}")
                return 'VerifyURL failed', 400
        except Exception as e:
            print(f"[回调] 验证异常: {e}")
            return jsonify({'code': 1, 'message': 'VerifyURL failed'}), 500

    elif request.method == 'POST':
        print("[回调] 收到 POST 请求，参数:", dict(request.args))
        valid, error = validate_base_params(request.args, ['msg_signature', 'timestamp', 'nonce'])
        if not valid:
            print(f"[回调] 参数校验失败: {error}")
            return jsonify({'code': 1, 'message': error}), 400

        msg_signature = request.args.get('msg_signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        post_data = request.data.decode('utf-8')

        print(f"[回调] POST参数: msg_signature={msg_signature}, timestamp={timestamp}, nonce={nonce}")
        print(f"[回调] 加密内容: {post_data}")

        try:
            import xmltodict
            # 1. 解析加密XML为dict，获取Encrypt字段
            xml_dict = xmltodict.parse(post_data)
            encrypt_msg = None
            # 兼容不同根节点
            if 'xml' in xml_dict and 'Encrypt' in xml_dict['xml']:
                encrypt_msg = xml_dict['xml']['Encrypt']
            if not encrypt_msg:
                print("[回调] 未找到Encrypt字段")
                return jsonify({'code': 1, 'message': 'No Encrypt field'}), 400
            print(f"[回调] 解析出Encrypt: {encrypt_msg}")


            # 2. 解密（只传Encrypt字段内容）
            ret, decrypted_xml = wxcpt.DecryptMsg(encrypt_msg, msg_signature, timestamp, nonce)
            if ret != 0:
                print(f"[回调] DecryptMsg失败: {ret}")
                return jsonify({'code': 1, 'message': 'DecryptMsg fail'}), 400

            print(f"[回调] 解密后的内容: {decrypted_xml}")

            # 3. 解析明文XML为dict，获取业务数据
            decrypted_dict = xmltodict.parse(decrypted_xml)
            info_type = None
            if 'xml' in decrypted_dict and 'InfoType' in decrypted_dict['xml']:
                info_type = decrypted_dict['xml']['InfoType']
            print(f"[回调] InfoType: {info_type}")

            if info_type == 'suite_ticket':
                suite_ticket = decrypted_dict['xml'].get('SuiteTicket')
                print(f"[回调] SuiteTicket: {suite_ticket}")
                save_suite_ticket(suite_ticket)
                suite_access_token = get_suite_access_token()
                if suite_access_token:
                    print(f"[回调] suite_access_token 获取成功: {suite_access_token}")
                else:
                    print(f"[回调] suite_access_token 获取失败")
            elif info_type == 'create_auth':
                auth_code = decrypted_dict['xml'].get('AuthCode')
                print(f"[回调] AuthCode: {auth_code}")
                global _auth_code
                _auth_code = auth_code
                from threading import Thread
                def async_get_permanent_code(auth_code):
                    try:
                        permanent_result = get_permanent_code(auth_code)
                        if permanent_result:
                            print("[回调] 永久授权码获取成功")
                        else:
                            print("[回调] 永久授权码获取失败")
                    except Exception as e:
                        print(f"[回调] 异步获取永久授权码异常: {e}")
                Thread(target=async_get_permanent_code, args=(auth_code,)).start()
                return 'success'
            else:
                print(f"[回调] 其他 InfoType: {info_type}")

            return 'success'

        except Exception as e:
            print(f"[回调] 解密或解析异常: {e}")
            return jsonify({'code': 1, 'message': 'Decrypt or parse failed'}), 500

    else:
        return 'Method Not Allowed', 405