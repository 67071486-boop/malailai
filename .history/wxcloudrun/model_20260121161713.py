from datetime import datetime

from wxcloudrun import db


# 计数表
class Counters(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'Counters'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=1)
    created_at = db.Column('createdAt', db.TIMESTAMP, nullable=False, server_default=db.text('CURRENT_TIMESTAMP'))
    updated_at = db.Column('updatedAt', db.TIMESTAMP, nullable=False, server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))


# 企业授权表
class CorpAuth(db.Model):
    __tablename__ = 'CorpAuth'

    id = db.Column(db.Integer, primary_key=True)
    corp_id = db.Column(db.String(64), unique=True, nullable=False)  # 企业ID
    permanent_code = db.Column(db.Text, nullable=False)  # 永久授权码
    auth_corp_info = db.Column(db.Text, nullable=True)  # 企业授权信息（JSON字符串）
    created_at = db.Column('createdAt', db.TIMESTAMP, nullable=False, server_default=db.text('CURRENT_TIMESTAMP'))
    updated_at = db.Column('updatedAt', db.TIMESTAMP, nullable=False, server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
