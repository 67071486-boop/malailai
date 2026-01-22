from flask import Blueprint, request
from wxcloudrun.services.callback_service import handle_data_callback, handle_command_callback

wxwork_bp = Blueprint("wxwork", __name__, url_prefix="/wxwork")


@wxwork_bp.route("/callback/data", methods=["GET", "POST"])
def callback_data():
    """企业微信数据回调，解密和分发由 callback_service 处理。"""
    return handle_data_callback(request)


@wxwork_bp.route("/callback/command", methods=["GET", "POST"])
def callback_command():
    """企业微信指令回调（suite_ticket、create_auth 等）。"""
    return handle_command_callback(request)