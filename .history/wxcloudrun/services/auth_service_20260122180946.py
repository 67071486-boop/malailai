import json
from threading import Thread
from typing import Optional, Tuple
import requests

from wxcloudrun.dao import query_corp_auth, insert_corp_auth, update_corp_auth
from wxcloudrun.model import new_corp_auth
from wxcloudrun.services.token_service import get_suite_access_token


def get_permanent_code(auth_code: str) -> Optional[Tuple[str, dict]]:
    """通过临时授权码获取永久授权码并落库。"""
    suite_token = get_suite_access_token()
    if not suite_token:
        return None

    url = (
        "https://qyapi.weixin.qq.com/cgi-bin/service/get_permanent_code"
        f"?suite_access_token={suite_token}"
    )
    payload = {"auth_code": auth_code}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        result = resp.json()
        if result.get("errcode", 0) != 0:
            return None
        permanent_code = result.get("permanent_code")
        auth_corp_info = result.get("auth_corp_info", {})
        corp_id = auth_corp_info.get("corpid")

        corp_auth = query_corp_auth(corp_id)
        if corp_auth:
            corp_auth["permanent_code"] = permanent_code
            corp_auth["auth_corp_info"] = json.dumps(auth_corp_info)
            update_corp_auth(corp_auth)
        else:
            corp_auth = new_corp_auth(
                corp_id=corp_id,
                permanent_code=permanent_code,
                auth_corp_info=json.dumps(auth_corp_info),
            )
            insert_corp_auth(corp_auth)

        return permanent_code, auth_corp_info
    except Exception:
        return None


def async_get_permanent_code(auth_code: str) -> None:
    """异步拉取永久授权码，避免阻塞回调。"""

    def _worker(code: str):
        try:
            get_permanent_code(code)
        except Exception:
            pass

    Thread(target=_worker, args=(auth_code,), daemon=True).start()


__all__ = ["get_permanent_code", "async_get_permanent_code"]
