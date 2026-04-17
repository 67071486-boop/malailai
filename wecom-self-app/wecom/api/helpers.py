from wecom.response import make_err_response
from wecom.services.service import token_service
import config


def _parse_int(value, default):
    try:
        return int(value)
    except Exception:
        return default


def _resolve_access_token(params):
    """根据 corp_id 获取自建应用 access_token。"""
    corp_id = params.get("corp_id") or config.WXWORK_CORP_ID
    if not corp_id:
        return None
    return token_service.get_corp_access_token(corp_id)


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


def _normalize_int_list(value):
    """将逗号或数组形式的值转换为 int 列表，若无法解析则返回 None。"""
    raw_values = _as_list(value)
    if not raw_values:
        return None
    normalized = []
    for item in raw_values:
        try:
            normalized.append(int(item))
        except (TypeError, ValueError):
            continue
    return normalized or None


def _require_str_param(params, key):
    """确保指定的请求参数存在并为非空字符串。"""
    value = params.get(key)
    if value is None:
        raise ValueError(f"{key} is required")
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{key} cannot be empty")
    return stripped


def _missing_token_response():
    return make_err_response("missing corp_id or unable to obtain access_token")
