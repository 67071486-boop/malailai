import time
import logging
import requests
from flask import Blueprint, request, jsonify

# 企业微信配置（建议从环境变量读取）
WXWORK_CORP_ID = "your_corp_id"  # 企业ID
WXWORK_CORP_SECRET = "your_corp_secret"  # 应用Secret
WXWORK_AGENT_ID = "your_agent_id"  # 应用ID

# Access Token 缓存
_access_token = None
_token_expires = 0

wxwork_bp = Blueprint("wxwork", __name__, url_prefix="/wxwork")

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

        if data.get("errcode") == 0:
            _access_token = data["access_token"]
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
            "text": {"content": content},
        }

        response = requests.post(url, json=data, timeout=10)
        result = response.json()

        if result.get("errcode") == 0:
            logger.info(f"消息发送成功: {user_id}")
            return True, "发送成功"
        else:
            logger.error(f"消息发送失败: {result}")
            return False, result.get("errmsg", "发送失败")
    except Exception as e:
        logger.error(f"发送消息异常: {e}")
        return False, str(e)


@wxwork_bp.route("/send_message", methods=["POST"])
def send_message():
    """发送企业微信消息 API"""
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        content = data.get("content")

        if not user_id or not content:
            return jsonify({"code": 1, "message": "缺少 user_id 或 content 参数"})

        success, message = send_text_message(user_id, content)

        if success:
            return jsonify({"code": 0, "message": message})
        else:
            return jsonify({"code": 1, "message": message})

    except Exception as e:
        logger.error(f"发送消息API异常: {e}")
        return jsonify({"code": 1, "message": "服务器内部错误"})


@wxwork_bp.route("/callback", methods=["POST"])
def callback():
    """企业微信回调处理"""
    try:
        # 这里处理企业微信推送的回调消息
        # 需要实现消息解密、验证等逻辑
        data = request.get_json()

        # TODO: 实现回调消息处理逻辑
        logger.info(f"收到回调消息: {data}")

        return jsonify({"code": 0, "message": "success"})

    except Exception as e:
        logger.error(f"回调处理异常: {e}")
        return jsonify({"code": 1, "message": "处理失败"})
