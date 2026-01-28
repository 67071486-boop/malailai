import logging
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import config

# MongoDB连接配置（从config读取，避免硬编码）
MONGO_URI = getattr(config, "MONGO_URI")
MONGO_DB_NAME = getattr(config, "MONGO_DB_NAME")
client = MongoClient(MONGO_URI)
db = client.get_database(MONGO_DB_NAME)

# 初始化日志
logger = logging.getLogger("log")

# 索引说明：
# - 适合加索引的场景：高频查询/排序、过滤条件选择性高、线上慢查询稳定复现。
# - 不建议加索引的场景：低频查询、低选择性字段（如布尔/状态很少种类）、写入高频且查询少。
# - 索引过多的影响：每次插入/更新都要维护索引结构，增加写入延迟；索引会占用额外存储与内存。


def ensure_indexes():
    """创建/确保必要索引存在。"""
    try:
        # group_chats：chat_id 精确查询（唯一）
        db.group_chats.create_index("chat_id", unique=True)
        # group_chats：按 corp_id + name 查询（订单号映射群名）
        db.group_chats.create_index([("corp_id", 1), ("name", 1)])

        # pending_order_qr：按状态+时间扫描（定时任务）
        db.pending_order_qr.create_index([("status", 1), ("created_at", 1)])
        # pending_order_qr：唯一定位一条待推送记录
        db.pending_order_qr.create_index(
            [("corp_id", 1), ("order_no", 1), ("external_userid", 1)],
            unique=True,
        )

        # corp_config_id：按 config_id 或 corp_id+chat_id 查询
        db.corp_config_id.create_index("config_id", unique=True)
        db.corp_config_id.create_index([("corp_id", 1), ("chat_id", 1)])

        # wecom_tokens：按 key 唯一索引
        db.wecom_tokens.create_index("key", unique=True)
    except PyMongoError as e:
        logger.info(f"ensure_indexes errorMsg= {e}")


def query_counterbyid(id):
    """
    根据ID查询Counter实体
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        return db.counters.find_one({"id": id})
    except PyMongoError as e:
        logger.info(f"query_counterbyid errorMsg= {e}")
        return None


def delete_counterbyid(id):
    """
    根据ID删除Counter实体
    :param id: Counter的ID
    """
    try:
        db.counters.delete_one({"id": id})
    except PyMongoError as e:
        logger.info(f"delete_counterbyid errorMsg= {e}")


def insert_counter(counter):
    """
    插入一个Counter实体
    :param counter: Counters实体
    """
    try:
        db.counters.insert_one(counter)
    except PyMongoError as e:
        logger.info(f"insert_counter errorMsg= {e}")


def update_counterbyid(counter):
    """
    根据ID更新counter的值
    :param counter实体
    """
    try:
        db.counters.update_one({"id": counter["id"]}, {"$set": counter})
    except PyMongoError as e:
        logger.info(f"update_counterbyid errorMsg= {e}")


def query_corp_auth(corp_id):
    """
    根据corp_id查询CorpAuth实体
    :param corp_id: 企业ID
    :return: CorpAuth实体
    """
    try:
        return db.corp_auth.find_one({"corp_id": corp_id})
    except PyMongoError as e:
        logger.info(f"query_corp_auth errorMsg= {e}")
        return None


def query_all_corp_auths():
    """
    查询所有 corp_auth 文档（返回列表）。
    注意：在数据量很大时应改为分页或使用游标。
    """
    try:
        return list(db.corp_auth.find({}))
    except PyMongoError as e:
        logger.info(f"query_all_corp_auths errorMsg= {e}")
        return []


def insert_corp_auth(corp_auth):
    """
    插入一个CorpAuth实体
    :param corp_auth: CorpAuth实体
    """
    try:
        db.corp_auth.insert_one(corp_auth)
    except PyMongoError as e:
        logger.info(f"insert_corp_auth errorMsg= {e}")


def update_corp_auth(corp_auth):
    """
    更新CorpAuth实体
    :param corp_auth: CorpAuth实体
    """
    try:
        db.corp_auth.update_one(
            {"corp_id": corp_auth["corp_id"]}, {"$set": corp_auth}, upsert=True
        )
    except PyMongoError as e:
        logger.info(f"update_corp_auth errorMsg= {e}")


# ===== 客户群（externalcontact groupchat）存储 =====


def upsert_group_chat(doc):
    """根据 chat_id upsert 客户群详情。"""
    try:
        chat_id = doc.get("chat_id")
        if not chat_id:
            raise ValueError("chat_id missing")
        db.group_chats.update_one({"chat_id": chat_id}, {"$set": doc}, upsert=True)
    except (PyMongoError, ValueError) as e:
        logger.info(f"upsert_group_chat errorMsg= {e}")


def mark_group_chat_dismissed(chat_id):
    """标记客户群为已解散。"""
    try:
        db.group_chats.update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "status_text": "dismissed",
                    "status_code": 3,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
    except PyMongoError as e:
        logger.info(f"mark_group_chat_dismissed errorMsg= {e}")


def query_group_chat(chat_id):
    """查询单个客户群记录。"""
    try:
        return db.group_chats.find_one({"chat_id": chat_id})
    except PyMongoError as e:
        logger.info(f"query_group_chat errorMsg= {e}")
        return None


def query_group_chat_by_name(corp_id, name):
    """根据 corp_id + 群名称查询客户群记录。"""
    try:
        return db.group_chats.find_one({"corp_id": corp_id, "name": name})
    except PyMongoError as e:
        logger.info(f"query_group_chat_by_name errorMsg= {e}")
        return None


def query_group_chats(filter_doc=None, *, limit=50, skip=0):
    """查询客户群列表（支持过滤/分页）。"""
    try:
        filter_doc = filter_doc or {}
        return list(db.group_chats.find(filter_doc).skip(skip).limit(limit))
    except PyMongoError as e:
        logger.info(f"query_group_chats errorMsg= {e}")
        return []


# ===== 微信客服（KF）消息游标存储 =====


def query_kf_cursor(open_kfid):
    """根据 open_kfid 查询游标记录。"""
    try:
        return db.kf_cursors.find_one({"open_kfid": open_kfid})
    except PyMongoError as e:
        logger.info(f"query_kf_cursor errorMsg= {e}")
        return None


def upsert_kf_cursor(doc):
    """根据 open_kfid upsert 游标记录。"""
    try:
        open_kfid = doc.get("open_kfid")
        if not open_kfid:
            raise ValueError("open_kfid missing")
        db.kf_cursors.update_one({"open_kfid": open_kfid}, {"$set": doc}, upsert=True)
    except (PyMongoError, ValueError) as e:
        logger.info(f"upsert_kf_cursor errorMsg= {e}")


# ===== corp_config_id 存储（join_way/contact_way） =====


def query_corp_config_by_chat(corp_id, chat_id):
    """根据 corp_id + chat_id 查询配置记录。"""
    try:
        return db.corp_config_id.find_one({"corp_id": corp_id, "chat_id": chat_id})
    except PyMongoError as e:
        logger.info(f"query_corp_config_by_chat errorMsg= {e}")
        return None


def upsert_corp_config(doc):
    """根据 config_id 或 corp_id+chat_id upsert 配置记录。"""
    try:
        config_id = doc.get("config_id")
        corp_id = doc.get("corp_id")
        chat_id = doc.get("chat_id")
        if config_id:
            filter_doc = {"config_id": config_id}
        else:
            if not corp_id or not chat_id:
                raise ValueError("corp_id/chat_id missing")
            filter_doc = {"corp_id": corp_id, "chat_id": chat_id}
        db.corp_config_id.update_one(filter_doc, {"$set": doc}, upsert=True)
    except (PyMongoError, ValueError) as e:
        logger.info(f"upsert_corp_config errorMsg= {e}")


# ===== 待推送订单二维码（pending_order_qr） =====


def upsert_pending_order(doc):
    """根据 corp_id+order_no+external_userid upsert 待推送记录。"""
    try:
        corp_id = doc.get("corp_id")
        order_no = doc.get("order_no")
        external_userid = doc.get("external_userid")
        if not corp_id or not order_no or not external_userid:
            raise ValueError("corp_id/order_no/external_userid missing")
        db.pending_order_qr.update_one(
            {"corp_id": corp_id, "order_no": order_no, "external_userid": external_userid},
            {"$set": doc},
            upsert=True,
        )
    except (PyMongoError, ValueError) as e:
        logger.info(f"upsert_pending_order errorMsg= {e}")


def query_pending_orders():
    """查询全部待推送记录列表（按创建时间升序）。"""
    try:
        return list(db.pending_order_qr.find({"status": "pending"}).sort("created_at", 1))
    except PyMongoError as e:
        logger.info(f"query_pending_orders errorMsg= {e}")
        return []


def query_pending_orders_paged(*, status="pending", limit=50, skip=0):
    """分页查询待推送记录（按创建时间升序）。"""
    try:
        return list(
            db.pending_order_qr.find({"status": status})
            .sort("created_at", 1)
            .skip(skip)
            .limit(limit)
        )
    except PyMongoError as e:
        logger.info(f"query_pending_orders_paged errorMsg= {e}")
        return []


def delete_expired_pending_orders(expired_before):
    """删除过期的待推送记录。"""
    try:
        db.pending_order_qr.delete_many(
            {"status": "pending", "created_at": {"$lt": expired_before}}
        )
    except PyMongoError as e:
        logger.info(f"delete_expired_pending_orders errorMsg= {e}")


def mark_pending_done(corp_id, order_no, external_userid, result=None):
    """标记待推送记录已完成。"""
    try:
        update = {"status": "done", "updated_at": datetime.utcnow()}
        if result is not None:
            update["result"] = result
        db.pending_order_qr.update_one(
            {"corp_id": corp_id, "order_no": order_no, "external_userid": external_userid},
            {"$set": update},
        )
    except PyMongoError as e:
        logger.info(f"mark_pending_done errorMsg= {e}")


# ===== 企微 token 持久化（suite/corp） =====


def save_suite_ticket(ticket: str):
    """保存 suite_ticket（不设置过期）。"""
    try:
        db.wecom_tokens.update_one(
            {"key": "suite_ticket"},
            {"$set": {"key": "suite_ticket", "value": ticket, "updated_at": datetime.utcnow()}},
            upsert=True,
        )
    except PyMongoError as e:
        logger.info(f"save_suite_ticket errorMsg= {e}")


def get_suite_ticket():
    try:
        doc = db.wecom_tokens.find_one({"key": "suite_ticket"})
        return doc.get("value") if doc else None
    except PyMongoError as e:
        logger.info(f"get_suite_ticket errorMsg= {e}")
        return None


def save_suite_access_token(token: str, expires_in: int):
    """保存 suite_access_token 及过期时间。"""
    try:
        expires_at = datetime.utcnow().timestamp() + expires_in - 300
        db.wecom_tokens.update_one(
            {"key": "suite_access_token"},
            {
                "$set": {
                    "key": "suite_access_token",
                    "value": token,
                    "expires_at": expires_at,
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )
    except PyMongoError as e:
        logger.info(f"save_suite_access_token errorMsg= {e}")


def get_suite_access_token():
    try:
        doc = db.wecom_tokens.find_one({"key": "suite_access_token"})
        if not doc:
            return None
        expires_at = doc.get("expires_at", 0)
        if expires_at and datetime.utcnow().timestamp() >= expires_at:
            return None
        return doc.get("value")
    except PyMongoError as e:
        logger.info(f"get_suite_access_token errorMsg= {e}")
        return None


def save_corp_access_token(corp_id: str, token: str, expires_in: int):
    """保存 corp access_token 及过期时间。"""
    try:
        expires_at = datetime.utcnow().timestamp() + expires_in - 300
        db.wecom_tokens.update_one(
            {"key": f"corp_access_token:{corp_id}"},
            {
                "$set": {
                    "key": f"corp_access_token:{corp_id}",
                    "corp_id": corp_id,
                    "value": token,
                    "expires_at": expires_at,
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )
    except PyMongoError as e:
        logger.info(f"save_corp_access_token errorMsg= {e}")


def get_corp_access_token(corp_id: str):
    try:
        doc = db.wecom_tokens.find_one({"key": f"corp_access_token:{corp_id}"})
        if not doc:
            return None
        expires_at = doc.get("expires_at", 0)
        if expires_at and datetime.utcnow().timestamp() >= expires_at:
            return None
        return doc.get("value")
    except PyMongoError as e:
        logger.info(f"get_corp_access_token errorMsg= {e}")
        return None


def _build_jsapi_ticket_key(corp_id: str, ticket_type: str, agent_id: str | None = None) -> str:
    if ticket_type == "agent":
        if not agent_id:
            raise ValueError("agent_id required for agent jsapi_ticket")
        return f"jsapi_ticket:agent:{corp_id}:{agent_id}"
    return f"jsapi_ticket:corp:{corp_id}"


def save_jsapi_ticket(corp_id: str, ticket: str, expires_in: int, *, ticket_type: str = "corp", agent_id: str | None = None):
    """保存 jsapi_ticket 及过期时间。"""
    try:
        key = _build_jsapi_ticket_key(corp_id, ticket_type, agent_id)
        expires_at = datetime.utcnow().timestamp() + expires_in - 300
        db.wecom_tokens.update_one(
            {"key": key},
            {
                "$set": {
                    "key": key,
                    "corp_id": corp_id,
                    "agent_id": agent_id,
                    "ticket_type": ticket_type,
                    "value": ticket,
                    "expires_at": expires_at,
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )
    except (PyMongoError, ValueError) as e:
        logger.info(f"save_jsapi_ticket errorMsg= {e}")


def get_jsapi_ticket(corp_id: str, *, ticket_type: str = "corp", agent_id: str | None = None):
    try:
        key = _build_jsapi_ticket_key(corp_id, ticket_type, agent_id)
        doc = db.wecom_tokens.find_one({"key": key})
        if not doc:
            return None
        expires_at = doc.get("expires_at", 0)
        if expires_at and datetime.utcnow().timestamp() >= expires_at:
            return None
        return doc.get("value")
    except (PyMongoError, ValueError) as e:
        logger.info(f"get_jsapi_ticket errorMsg= {e}")
        return None
