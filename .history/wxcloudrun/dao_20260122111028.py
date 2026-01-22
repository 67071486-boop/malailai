import logging
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# MongoDB连接配置
MONGO_URI = "mongodb://root:Ghh15377167407@dds-bp1fe7f6fab92cf41198-pub.mongodb.rds.aliyuncs.com:3717,dds-bp1fe7f6fab92cf42736-pub.mongodb.rds.aliyuncs.com:3717/wecom-development?replicaSet=mgset-97621859"
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
