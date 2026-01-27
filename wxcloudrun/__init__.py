from flask import Flask
import config
from wxcloudrun.dao import ensure_indexes

# 初始化web应用
app = Flask(__name__, instance_relative_config=True)
app.config["DEBUG"] = getattr(config, "DEBUG", False)

# 加载控制器
from wxcloudrun import views
from wxcloudrun import wxwork
from wxcloudrun.api import api_bp
from wxcloudrun.services.scheduler import init_scheduler

# 注册企业微信蓝图
app.register_blueprint(wxwork.wxwork_bp)
# 注册前端 API 蓝图
app.register_blueprint(api_bp)

# 加载配置
app.config.from_object("config")

# 启动后台调度器（用于主动同步占位任务）
init_scheduler(app)

# 初始化索引（如已有索引则跳过）
ensure_indexes()
