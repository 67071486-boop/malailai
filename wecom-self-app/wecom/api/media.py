import os
import tempfile

from flask import Response, request

from wecom.api import api_bp
from wecom.api.helpers import _missing_token_response, _resolve_access_token
from wecom.response import make_err_response, make_succ_response
from wecom.services.wecom.media_api import get_temp_media, upload_temp_media
from wecom.services.wecom_client import WeComApiError


@api_bp.route("/media/upload_temp", methods=["POST"])
def api_upload_temp_media():
    """测试入口：上传临时素材，返回 media_id/type/created_at。"""
    params = request.form.to_dict()
    file = request.files.get("file")
    media_type = params.get("type", "file")

    if not file:
        return make_err_response("file is required in form-data with key 'file'")

    access_token = _resolve_access_token(params)
    if not access_token:
        return _missing_token_response()

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            file.save(tmp_path)
        data = upload_temp_media(
            access_token,
            media_type,
            tmp_path,
            filename=file.filename,
            content_type=file.mimetype,
        )
        return make_succ_response(data)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


@api_bp.route("/media/get_temp", methods=["GET"])
def api_get_temp_media():
    """测试入口：根据 media_id 获取临时素材并回传给前端（支持 Range）。"""
    params = request.args.to_dict()
    media_id = params.get("media_id")
    if not media_id:
        return make_err_response("media_id is required")

    access_token = _resolve_access_token(params)
    if not access_token:
        return _missing_token_response()

    range_header = request.headers.get("Range") or params.get("range")

    try:
        resp = get_temp_media(access_token, media_id, range_header=range_header, stream=True)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))

    ctype = resp.headers.get("Content-Type", "application/octet-stream")
    flask_resp = Response(resp.iter_content(chunk_size=8192), status=resp.status_code, mimetype=ctype)
    content_length = resp.headers.get("Content-Length")
    if content_length:
        flask_resp.headers["Content-Length"] = content_length
    content_disp = resp.headers.get("Content-Disposition")
    if content_disp:
        flask_resp.headers["Content-Disposition"] = content_disp
    if resp.headers.get("Content-Range"):
        flask_resp.headers["Content-Range"] = resp.headers["Content-Range"]
    if resp.headers.get("Accept-Ranges"):
        flask_resp.headers["Accept-Ranges"] = resp.headers["Accept-Ranges"]
    return flask_resp