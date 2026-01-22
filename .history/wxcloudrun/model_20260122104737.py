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
#   "auth_corp_info": str,  # 企业授权信息（JSON字符串）
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
