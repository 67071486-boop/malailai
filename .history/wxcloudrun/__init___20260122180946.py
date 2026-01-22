from flask import Flask
import config

# 初始化web应用
app = Flask(__name__, instance_relative_config=True)
app.config["DEBUG"] = getattr(config, "DEBUG", False)

# 加载控制器
from wxcloudrun import views
from wxcloudrun import wxwork
from wxcloudrun.services.scheduler import init_scheduler

# 注册企业微信蓝图
app.register_blueprint(wxwork.wxwork_bp)

# 加载配置
app.config.from_object("config")

# 启动后台调度器（用于主动同步占位任务）
init_scheduler(app)
