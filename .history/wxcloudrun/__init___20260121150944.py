from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
import config
from sqlalchemy import create_engine, text

# 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLDB库
pymysql.install_as_MySQLdb()

# 初始化web应用
app = Flask(__name__, instance_relative_config=True)
app.config["DEBUG"] = config.DEBUG

# 创建数据库如果不存在
server_uri = "mysql://{}:{}@{}".format(
    config.username, config.password, config.db_address
)
engine = create_engine(server_uri)
with engine.connect() as conn:
    conn.execute(text("CREATE DATABASE IF NOT EXISTS flask_demo"))
    conn.commit()

# 设定数据库链接
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://{}:{}@{}/flask_demo".format(
    config.username, config.password, config.db_address
)

# 初始化DB操作对象
db = SQLAlchemy(app)

# 加载控制器
from wxcloudrun import views
from wxcloudrun import wxwork

# 注册企业微信蓝图
app.register_blueprint(wxwork.wxwork_bp)

# 加载配置
app.config.from_object("config")
