# Counters 文档结构示例
# {
#   "id": int,           # 计数器ID
#   "count": int,        # 计数值
#   "created_at": datetime, # 创建时间
#   "updated_at": datetime  # 更新时间
# }

# CorpAuth 文档结构示例
# {
#   "corp_id": str,         # 企业ID
#   "permanent_code": str,  # 永久授权码
#   "auth_corp_info": dict, # 企业授权信息（对象/子文档）
#   "created_at": datetime, # 创建时间
#   "updated_at": datetime  # 更新时间
# }

# 可选：定义工具函数生成文档
from datetime import datetime


def new_counter(id, count=1):
    now = datetime.utcnow()
    return {"id": id, "count": count, "created_at": now, "updated_at": now}


def new_corp_auth(corp_id, permanent_code, auth_corp_info=None):
    now = datetime.utcnow()
    return {
        "corp_id": corp_id,
        "permanent_code": permanent_code,
        "auth_corp_info": auth_corp_info,
        "created_at": now,
        "updated_at": now,
    }


def new_kf_cursor(open_kfid, cursor=None, corp_id=None):
    now = datetime.utcnow()
    doc = {
        "open_kfid": open_kfid,
        "cursor": cursor,
        "created_at": now,
        "updated_at": now,
    }
    if corp_id:
        doc["corp_id"] = corp_id
    return doc


def new_pending_order(corp_id, order_no, external_userid, open_kfid):
    now = datetime.utcnow()
    return {
        "corp_id": corp_id,
        "order_no": order_no,
        "external_userid": external_userid,
        "open_kfid": open_kfid,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }


def new_kf_welcome(corp_id, msgtype, payload, open_kfid=None):
    now = datetime.utcnow()
    return {
        "corp_id": corp_id,
        "open_kfid": open_kfid,
        "msgtype": msgtype,
        "payload": payload,
        "created_at": now,
        "updated_at": now,
    }
