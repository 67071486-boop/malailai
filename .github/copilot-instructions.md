# 微信云托管 Flask 计数器服务 - AI 助手指导说明

## 架构概述
这是一个基于 Flask 的简单计数器服务，用于微信云托管，具有模块化结构：
- **wxcloudrun/**：主应用包，包含视图、DAO、模型和响应工具
- **单计数器模式**：使用 ID=1 作为全局计数器实例
- **MySQL 集成**：通过 `config.py` 进行环境变量数据库配置
- **企业微信集成**：新增 `wxwork.py` 模块，支持企业微信消息发送和回调处理
- **应用初始化**：在 `wxcloudrun/__init__.py` 中完成 Flask 应用、SQLAlchemy 数据库和 Blueprint 注册

## 关键模式与约定

### 应用初始化流程
应用在 `wxcloudrun/__init__.py` 中初始化，遵循以下顺序：
```python
# 1. 使用 pymysql 替代 MySQLDB（Python3 兼容）
pymysql.install_as_MySQLdb()
# 2. 创建 Flask app 和 SQLAlchemy db 实例
app = Flask(__name__, instance_relative_config=True)
db = SQLAlchemy(app)
# 3. 导入视图和蓝图（必须在 db 初始化后）
from wxcloudrun import views, wxwork
# 4. 注册蓝图
app.register_blueprint(wxwork.wxwork_bp)
```

### 数据库操作
始终使用 DAO 模式，避免直接操作 db.session：
```python
from wxcloudrun.dao import query_counterbyid, insert_counter, update_counterbyid, delete_counterbyid
# 单计数器始终查询 ID=1
counter = query_counterbyid(1)
```

**关键实现细节**：
- DAO 方法使用 `try-except OperationalError` 捕获数据库错误
- `update_counterbyid()` 实现有误：应直接更新传入的 counter 对象，而非重新查询
- 更新操作需调用 `db.session.commit()` 提交事务
- 视图层负责创建/修改 Model 实例，DAO 仅负责持久化

### 企业微信操作
使用企业微信工具类，配置在代码中硬编码（应迁移到环境变量）：
```python
from wxcloudrun.wxwork import send_text_message, get_access_token
# 发送消息
success, message = send_text_message("user_id", "消息内容")
# 获取Access Token（自动缓存7200秒）
token = get_access_token()
```

**配置注意**：`wxwork.py` 中的 `WXWORK_CORP_ID`、`WXWORK_CORP_SECRET`、`WXWORK_AGENT_ID` 需从环境变量读取

### 响应格式化
始终使用响应工具构建一致的 API 响应：
```python
from wxcloudrun.response import make_succ_response, make_err_response, make_succ_empty_response
return make_succ_response(counter.count)  # 成功响应（带数据）
return make_err_response('缺少action参数')  # 错误响应
return make_succ_empty_response()  # 成功响应（无数据）
```

**响应格式**：
- 成功：`{"code": 0, "data": <任意值>}`
- 失败：`{"code": -1, "errorMsg": "错误信息"}`

### API 路由结构
- `GET /`：返回主页模板 `index.html`
- `GET /api/count`：获取当前计数（计数器不存在时返回 0）
- `POST /api/count`：使用 `{"action": "inc"}` 或 `{"action": "clear"}` 更新计数器
- `POST /wxwork/send_message`：发送企业微信消息
- `POST /wxwork/callback`：处理企业微信回调（开发中）

### 开发工作流
- **本地运行**：`python run.py 127.0.0.1 5000`（必须提供 host 和 port 参数）
- **数据库配置**：环境变量 `MYSQL_USERNAME`、`MYSQL_PASSWORD`、`MYSQL_ADDRESS`（格式：`host:port`）
- **数据库名称**：固定为 `flask_demo`（在 `__init__.py` 中硬编码）
- **企业微信配置**：需在 `wxwork.py` 中配置或改为从环境变量读取
- **调试模式**：在 `config.py` 中设置 `DEBUG = True`

### 代码组织
- **run.py**：应用入口，从命令行参数获取 host/port
- **config.py**：环境变量配置（数据库凭证、DEBUG 模式）
- **wxcloudrun/__init__.py**：应用初始化、数据库配置、蓝图注册
- **wxcloudrun/views.py**：主路由处理器和业务逻辑（使用 `@app.route` 装饰器）
- **wxcloudrun/wxwork.py**：企业微信 Blueprint（使用 `@wxwork_bp.route` 装饰器）
- **wxcloudrun/dao.py**：数据库访问层（包含日志记录）
- **wxcloudrun/model.py**：SQLAlchemy 模型（Counters 表定义）
- **wxcloudrun/response.py**：标准化 JSON 响应构建器
- **wxcloudrun/templates/index.html**：前端主页模板

## 重要注意事项
- 计数器在首次自增时自动创建（如果不存在），视图层负责构造完整的 Counter 对象
- 清零操作会完全删除计数器记录（调用 `delete_counterbyid(1)`）
- 所有时间戳使用 `datetime.now()` 设置 `created_at`/`updated_at`
- 企业微信 Access Token 自动缓存和管理（7200秒有效期，提前5分钟刷新）
- 扩展路由时遵循 Flask Blueprint 模式（参考 `wxwork.py`）
- **已知问题**：`dao.py` 中的 `update_counterbyid()` 逻辑有误，需重新查询后才能更新

## 新增路由示例
添加新蓝图路由：
```python
# 在 wxcloudrun/your_module.py 中
from flask import Blueprint
your_bp = Blueprint('your_name', __name__, url_prefix='/your_prefix')

@your_bp.route('/endpoint', methods=['POST'])
def your_handler():
    # 业务逻辑
    return make_succ_response(data)

# 在 wxcloudrun/__init__.py 中注册
from wxcloudrun import your_module
app.register_blueprint(your_module.your_bp)
```