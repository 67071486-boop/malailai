from flask import request

from wxcloudrun.api import api_bp
from wxcloudrun.response import make_err_response, make_succ_response
from wxcloudrun.services.wecom_client import WeComApiError, get_suite_client


@api_bp.route("/suite/getuserinfo3rd", methods=["GET", "POST"])
def api_suite_getuserinfo3rd():
    """前端调用：通过 code 获取第三方临时用户信息。"""
    params = request.get_json(silent=True) or {}
    code = params.get("code") or request.args.get("code")
    if not code:
        return make_err_response("code is required")

    try:
        suite = get_suite_client()
        data = suite.getuserinfo3rd(code)
        return make_succ_response(data)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))