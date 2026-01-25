from datetime import datetime
from flask import render_template, request, Response
from run import app
from wxcloudrun.dao import (
    delete_counterbyid,
    query_counterbyid,
    insert_counter,
    update_counterbyid,
)
from wxcloudrun.model import new_counter
from wxcloudrun.response import (
    make_succ_empty_response,
    make_succ_response,
    make_err_response,
)
import json
from wxcloudrun.dao import query_all_corp_auths, update_corp_auth
from wxcloudrun.services.wecom_client import fetch_auth_info, WeComApiError, get_contact_manager
from wxcloudrun.services import token_service
from wxcloudrun.services.wecom.media_api import upload_temp_media, get_temp_media
from wxcloudrun.services.wecom.kf.account_manager import KfAccountApi
from wxcloudrun.services.wecom.kf.servicer_manager import KfStaffApi
import tempfile
import os

kf_account_api = KfAccountApi()
kf_staff_api = KfStaffApi()


@app.route("/")
def index():
    """
    :return: 返回index页面
    """
    return render_template("index.html")


@app.route("/api/count", methods=["POST"])
def count():
    """
    :return:计数结果/清除结果
    """
    print("[views] /api/count POST请求进来", flush=True)
    # 获取请求体参数
    params = request.get_json(silent=True) or {}

    # 检查action参数
    if "action" not in params:
        return make_err_response("缺少action参数")

    # 按照不同的action的值，进行不同的操作
    action = params["action"]

    # 执行自增操作
    if action == "inc":
        counter = query_counterbyid(1)
        if counter is None:
            counter = new_counter(1, 1)
            insert_counter(counter)
        else:
            counter["count"] += 1
            counter["updated_at"] = datetime.utcnow()
            update_counterbyid(counter)
        return make_succ_response(counter["count"])

    # 执行清0操作
    elif action == "clear":
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response("action参数错误")


@app.route("/api/count", methods=["GET"])
def get_count():
    """
    :return: 计数的值
    """
    counter = query_counterbyid(1)
    return (
        make_succ_response(0)
        if counter is None
        else make_succ_response(counter["count"])
    )


@app.route("/api/update_corp_auths", methods=["POST"])
def update_corp_auths():
    """批量更新 `corp_auth` 集合中的授权信息：

    - 遍历所有 corp_auth 文档，使用 `permanent_code` 调用 `fetch_auth_info` 拉取 v2 授权信息
    - 将 v2 响应（JSON 字符串）写回 `auth_corp_info`，并更新 `updated_at`
    返回：成功/失败统计与错误列表
    """
    results = {"updated": 0, "failed": 0, "errors": []}
    docs = query_all_corp_auths()
    for doc in docs:
        try:
            corp_id = doc.get("corp_id")
            permanent_code = doc.get("permanent_code")
            if not corp_id or not permanent_code:
                results["failed"] += 1
                results["errors"].append({"corp_id": corp_id, "error": "missing corp_id or permanent_code"})
                continue
            v2 = fetch_auth_info(corp_id, permanent_code)
            # 保存为 JSON 字符串（与现有字段格式兼容）
            doc["auth_corp_info"] = json.dumps(v2)
            doc["updated_at"] = datetime.utcnow()
            update_corp_auth(doc)
            results["updated"] += 1
        except WeComApiError as e:
            results["failed"] += 1
            results["errors"].append({"corp_id": doc.get("corp_id"), "error": str(e)})
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"corp_id": doc.get("corp_id"), "error": str(e)})
    return make_succ_response(results)


@app.route("/api/department/simplelist", methods=["POST"])
def department_simplelist():
    """测试接口：调用 ContactManager.simplelist_departments，返回部门 ID 列表。

    请求示例：{"access_token": "...", "id": 1}
    """
    try:
        params = request.get_json() or {}
        access_token = params.get("access_token")
        dept_id = params.get("id")
        corp_id = params.get("corp_id")

        # 如果前端未提供 access_token，则尝试通过 corp_id 或者数据库中第一个 corp_auth 获取 permanent_code 并拉取 access_token
        if not access_token:
            # 优先使用请求中提供的 corp_id
            corp_doc = None
            if corp_id:
                # 从数据库查找匹配 corp_id
                all_docs = query_all_corp_auths()
                for d in all_docs:
                    if d.get("corp_id") == corp_id:
                        corp_doc = d
                        break
            # 若未提供或未找到，则使用第一条记录作为回退
            if corp_doc is None:
                all_docs = query_all_corp_auths()
                if not all_docs:
                    return make_err_response("no corp_auth records available to obtain access_token")
                corp_doc = all_docs[0]

            permanent_code = corp_doc.get("permanent_code")
            corp_id = corp_doc.get("corp_id")
            if not permanent_code or not corp_id:
                return make_err_response("corp_auth record missing corp_id or permanent_code")

            access_token = token_service.get_corp_access_token(corp_id, permanent_code)
            if not access_token:
                return make_err_response("unable to obtain access_token for corp_id=" + str(corp_id))

        cm = get_contact_manager()
        data = cm.simplelist_departments(access_token, id=dept_id)
        return make_succ_response(data)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


def _resolve_access_token(params):
    """从请求参数中解析 access_token；若缺失则尝试通过 corp_id 或首条 corp_auth 获取。"""
    access_token = params.get("access_token")
    if access_token:
        return access_token

    corp_id = params.get("corp_id")
    corp_doc = None
    all_docs = query_all_corp_auths()
    if corp_id:
        for d in all_docs:
            if d.get("corp_id") == corp_id:
                corp_doc = d
                break
    if corp_doc is None and all_docs:
        corp_doc = all_docs[0]

    if not corp_doc:
        return None
    permanent_code = corp_doc.get("permanent_code")
    corp_id = corp_doc.get("corp_id")
    if not permanent_code or not corp_id:
        return None
    return token_service.get_corp_access_token(corp_id, permanent_code)


def _as_list(value, cast=None):
    """将字符串(逗号分隔)/列表标准化为列表；可选类型转换。"""
    if value is None:
        return None
    if isinstance(value, str):
        items = [v.strip() for v in value.split(",") if v.strip()]
    elif isinstance(value, list):
        items = [v for v in value if v is not None]
    else:
        return None
    if cast:
        converted = []
        for v in items:
            try:
                converted.append(cast(v))
            except Exception:
                continue
        return converted or None
    return items or None


@app.route("/api/kf/account/add", methods=["POST"])
def api_kf_account_add():
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return make_err_response("missing access_token and no corp_auth fallback")
    try:
        data = kf_account_api.add_account(access_token, params.get("name"), params.get("media_id"))
        return make_succ_response(data)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@app.route("/api/kf/account/del", methods=["POST"])
def api_kf_account_del():
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return make_err_response("missing access_token and no corp_auth fallback")
    try:
        data = kf_account_api.delete_account(access_token, params.get("open_kfid"))
        return make_succ_response(data)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@app.route("/api/kf/account/update", methods=["POST"])
def api_kf_account_update():
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return make_err_response("missing access_token and no corp_auth fallback")
    try:
        data = kf_account_api.update_account(
            access_token,
            params.get("open_kfid"),
            name=params.get("name"),
            media_id=params.get("media_id"),
        )
        return make_succ_response(data)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@app.route("/api/kf/account/list", methods=["POST"])
def api_kf_account_list():
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return make_err_response("missing access_token and no corp_auth fallback")
    try:
        offset = int(params.get("offset", 0) or 0)
        limit = int(params.get("limit", 20) or 20)
    except Exception:
        return make_err_response("offset/limit must be numbers")
    try:
        data = kf_account_api.list_accounts(access_token, offset=offset, limit=limit)
        return make_succ_response(data)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@app.route("/api/kf/account/contact_way", methods=["POST"])
def api_kf_account_contact_way():
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return make_err_response("missing access_token and no corp_auth fallback")
    try:
        data = kf_account_api.get_contact_way(
            access_token,
            params.get("open_kfid"),
            scene=params.get("scene"),
        )
        return make_succ_response(data)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@app.route("/api/kf/servicer/list", methods=["POST"])
def api_kf_servicer_list():
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return make_err_response("missing access_token and no corp_auth fallback")
    try:
        data = kf_staff_api.list_staffs(access_token, params.get("open_kfid"))
        return make_succ_response(data)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@app.route("/api/kf/servicer/add", methods=["POST"])
def api_kf_servicer_add():
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return make_err_response("missing access_token and no corp_auth fallback")
    user_ids = _as_list(params.get("userid_list"))
    dept_ids = _as_list(params.get("department_id_list"), cast=int)
    try:
        data = kf_staff_api.add_staffs(
            access_token,
            params.get("open_kfid"),
            user_ids=user_ids,
            department_ids=dept_ids,
        )
        return make_succ_response(data)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@app.route("/api/kf/servicer/del", methods=["POST"])
def api_kf_servicer_del():
    params = request.get_json() or {}
    access_token = _resolve_access_token(params)
    if not access_token:
        return make_err_response("missing access_token and no corp_auth fallback")
    user_ids = _as_list(params.get("userid_list"))
    dept_ids = _as_list(params.get("department_id_list"), cast=int)
    try:
        data = kf_staff_api.del_staffs(
            access_token,
            params.get("open_kfid"),
            user_ids=user_ids,
            department_ids=dept_ids,
        )
        return make_succ_response(data)
    except WeComApiError as e:
        return make_err_response(str(e))
    except Exception as e:
        return make_err_response(str(e))


@app.route("/api/media/upload_temp", methods=["POST"])
def api_upload_temp_media():
    """测试入口：上传临时素材，返回 media_id/type/created_at。"""
    params = request.form.to_dict()
    file = request.files.get("file")
    media_type = params.get("type", "file")

    if not file:
        return make_err_response("file is required in form-data with key 'file'")

    access_token = _resolve_access_token(params)
    if not access_token:
        return make_err_response("missing access_token and no corp_auth fallback")

    # 将上传内容暂存到临时文件以复用 media_api 的文件路径接口
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


@app.route("/api/media/get_temp", methods=["GET"])
def api_get_temp_media():
    """测试入口：根据 media_id 获取临时素材并回传给前端（支持 Range）。"""
    params = request.args.to_dict()
    media_id = params.get("media_id")
    if not media_id:
        return make_err_response("media_id is required")

    access_token = _resolve_access_token(params)
    if not access_token:
        return make_err_response("missing access_token and no corp_auth fallback")

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
    # 透传分片下载相关头
    if resp.headers.get("Content-Range"):
        flask_resp.headers["Content-Range"] = resp.headers["Content-Range"]
    if resp.headers.get("Accept-Ranges"):
        flask_resp.headers["Accept-Ranges"] = resp.headers["Accept-Ranges"]
    return flask_resp


@app.route("/media/test", methods=["GET"])
def media_test_page():
    """简单的素材上传/下载测试页面。"""
    return render_template("media_test.html")


@app.route('/kf/test')
def kf_test():
    return render_template('kf_test.html')
