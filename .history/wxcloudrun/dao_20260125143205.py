import logging
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import config

# MongoDB连接配置（从config读取，避免硬编码）
MONGO_URI = getattr(config, "MONGO_URI", None)
client = MongoClient(MONGO_URI)
db = client.get_database("wecom-development")

# 初始化日志
logger = logging.getLogger("log")


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
