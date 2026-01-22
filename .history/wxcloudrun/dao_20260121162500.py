import logging

from sqlalchemy.exc import OperationalError

from wxcloudrun import db
from wxcloudrun.model import Counters, CorpAuth

# 初始化日志
logger = logging.getLogger("log")


def query_counterbyid(id):
    """
    根据ID查询Counter实体
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        return Counters.query.filter(Counters.id == id).first()
    except OperationalError as e:
        logger.info("query_counterbyid errorMsg= {} ".format(e))
        return None


def delete_counterbyid(id):
    """
    根据ID删除Counter实体
    :param id: Counter的ID
    """
    try:
        counter = Counters.query.get(id)
        if counter is None:
            return
        db.session.delete(counter)
        db.session.commit()
    except OperationalError as e:
        logger.info("delete_counterbyid errorMsg= {} ".format(e))


def insert_counter(counter):
    """
    插入一个Counter实体
    :param counter: Counters实体
    """
    try:
        db.session.add(counter)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_counter errorMsg= {} ".format(e))


def update_counterbyid(counter):
    """
    根据ID更新counter的值
    :param counter实体
    """
    try:
        counter = query_counterbyid(counter.id)
        if counter is None:
            return
        db.session.flush()
        db.session.commit()
    except OperationalError as e:
        logger.info("update_counterbyid errorMsg= {} ".format(e))


def query_corp_auth(corp_id):
    """
    根据corp_id查询CorpAuth实体
    :param corp_id: 企业ID
    :return: CorpAuth实体
    """
    try:
        return CorpAuth.query.filter(CorpAuth.corp_id == corp_id).first()
    except OperationalError as e:
        logger.info("query_corp_auth errorMsg= {} ".format(e))
        return None


def insert_corp_auth(corp_auth):
    """
    插入一个CorpAuth实体
    :param corp_auth: CorpAuth实体
    """
    try:
        db.session.add(corp_auth)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_corp_auth errorMsg= {} ".format(e))


def update_corp_auth(corp_auth):
    """
    更新CorpAuth实体
    :param corp_auth: CorpAuth实体
    """
    try:
        db.session.merge(corp_auth)
        db.session.commit()
    except OperationalError as e:
        logger.info("update_corp_auth errorMsg= {} ".format(e))
