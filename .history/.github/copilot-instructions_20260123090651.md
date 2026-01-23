# 微信云托管 Flask 服务 - AI 助手指导说明

## 架构概述
这是一个基于 Flask 的微信云托管项目，集成了计数器服务和企业微信第三方应用开发功能：
- **数据层**：MongoDB（已从 MySQL 迁移），使用 PyMongo 直接操作文档
- **应用层**：Flask + Blueprint 模块化路由（views.py、wxwork.py）
- **企业微信集成**：支持第三方应用授权、消息加解密、回调处理
- **配置管理**：环境变量（python-dotenv）+ 硬编码配置（需迁移）

## 数据库架构（MongoDB）

### 连接配置
```python
# config.py 中定义 MONGO_URI
# dao.py 中实际连接
client = MongoClient(MONGO_URI)
db = client.get_database("wecom-development")
```

**重要**：`dao.py` 中的连接字符串硬编码，应改为从 `config.MONGO_URI` 读取

### 文档模型（非 Schema）
```python
# counters 集合（计数器）
{"id": int, "count": int, "created_at": datetime, "updated_at": datetime}

# corp_auth 集合（企业授权）
{"corp_id": str, "permanent_code": str, "auth_corp_info": str, "created_at": datetime, "updated_at": datetime}
```

### DAO 模式
始终使用 DAO 层访问数据库，避免在视图中直接调用 PyMongo：
```python
from wxcloudrun.dao import query_counterbyid, insert_counter, update_counterbyid, delete_counterbyid
counter = query_counterbyid(1)  # 返回 dict 或 None
```

**关键差异**：
- 返回值是原生 dict（非 ORM 对象），直接用 `counter["count"]` 访问
- 更新操作：`update_counterbyid(counter)` 使用 `$set` 全量更新传入的 dict
- 错误处理：捕获 `PyMongoError` 而非 `OperationalError`

## 企业微信第三方应用开发

### 配置（环境变量）
```python
# wxwork.py 从环境变量读取（需在 .env 或云托管环境变量中设置）
WXWORK_CORP_ID          # 企业 ID
WXWORK_SUITE_ID         # 第三方应用 SuiteID
WXWORK_SUITE_SECRET     # 第三方应用 Secret
WXWORK_TOKEN            # 回调 Token
WXWORK_ENCODING_AES_KEY # 回调加密 AES Key
```

### 授权流程（关键）
```python
# 1. 企业微信推送 suite_ticket → /wxwork/callback/command
# 2. 服务端缓存 suite_ticket（内存，生产需用 Redis/DB）
# 3. 使用 suite_ticket 获取 suite_access_token（缓存7200秒）
# 4. 企业授权后推送 auth_code → /wxwork/callback/command
# 5. 异步调用 get_permanent_code(auth_code) 获取永久授权码
# 6. 永久授权码存入 corp_auth 集合
```

### 回调处理模式
```python
# GET 请求：URL 验证
wxcpt = WXBizMsgCrypt(TOKEN, AES_KEY, sReceiveId)
ret, sEchoStr = wxcpt.VerifyURL(msg_signature, timestamp, nonce, echostr)
return sEchoStr  # 返回解密后的明文 echostr

# POST 请求：消息解密
# 1. 动态提取 ToUserName 作为 sReceiveId（正则匹配 XML）
# 2. 使用 WXBizMsgCrypt.DecryptMsg 解密
# 3. xmltodict.parse 转换为 dict
# 4. 根据 InfoType 分发处理逻辑（suite_ticket、create_auth）
```

**关键实现**：`wechat_official/WXBizMsgCrypt.py` 封装了加解密逻辑（pycryptodome 依赖）

### Token 缓存机制
```python
# 全局变量缓存（生产环境应改用 Redis）
_suite_ticket = None  # 手动保存，无过期时间
_suite_access_token = None  # 自动缓存7200秒，提前5分钟刷新
```

## API 路由结构

### 核心路由（views.py）
- `GET /`：返回 `index.html` 主页
- `GET /api/count`：获取计数器（不存在返回0）
- `POST /api/count`：`{"action": "inc|clear"}` 自增或清零

### 企业微信路由（wxwork.py Blueprint）
- `POST /wxwork/callback/command`：指令回调（suite_ticket、create_auth）
- `POST /wxwork/callback/data`：数据回调（用户消息、事件）

**路由注册**：在 `wxcloudrun/__init__.py` 中 `app.register_blueprint(wxwork.wxwork_bp)`

## 响应格式标准
```python
from wxcloudrun.response import make_succ_response, make_err_response, make_succ_empty_response

# 成功（带数据）
return make_succ_response(counter["count"])  # {"code": 0, "data": 42}

# 失败
return make_err_response('缺少action参数')  # {"code": -1, "errorMsg": "..."}

# 成功（无数据）
return make_succ_empty_response()  # {"code": 0}
```

## 开发工作流

### 本地运行
```bash
# 必须提供 host 和 port 参数
python run.py 127.0.0.1 5000
```

### 环境变量（.env 文件）
```ini
MONGO_URI=mongodb://user:pass@host:port/admin?replicaSet=...
WXWORK_SUITE_ID=...
WXWORK_SUITE_SECRET=...
WXWORK_TOKEN=...
WXWORK_ENCODING_AES_KEY=...
```

### 调试模式
在 `config.py` 中设置 `DEBUG = True`（已默认开启）

### 依赖安装
```bash
pip install -r requirements.txt
# 关键依赖：Flask, pymongo, pycryptodome, xmltodict, requests
```

## 代码组织

### 关键文件
<!-- - [run.py](run.py)：应用入口，解析命令行参数启动 Flask
- [config.py](config.py)：环境变量配置（MONGO_URI、DEBUG）
<!-- - [wxcloudrun/__init__.py](wxcloudrun/__init__.py)：Flask 应用初始化、蓝图注册 -->
- [wxcloudrun/dao.py](wxcloudrun/dao.py)：MongoDB 访问层（PyMongo + 日志）
- [wxcloudrun/model.py](wxcloudrun/model.py)：文档构造函数（`new_counter`、`new_corp_auth`）
- [wxcloudrun/views.py](wxcloudrun/views.py)：计数器 API 路由（`@app.route`）
- [wxcloudrun/wxwork.py](wxcloudrun/wxwork.py)：企业微信 Blueprint（`@wxwork_bp.route`）
- [wxcloudrun/wechat_official/](wxcloudrun/wechat_official/)：企业微信加解密库（WXBizMsgCrypt） -->

### Blueprint 扩展模式
```python
# 1. 创建 wxcloudrun/your_module.py
from flask import Blueprint
your_bp = Blueprint('your_name', __name__, url_prefix='/your_prefix')

@your_bp.route('/endpoint', methods=['POST'])
def your_handler():
    return make_succ_response(data)

# 2. 在 wxcloudrun/__init__.py 注册
from wxcloudrun import your_module
app.register_blueprint(your_module.your_bp)
```

## 已知问题与改进建议
- **硬编码连接**：`dao.py` 中的 `MONGO_URI` 应从 `config.py` 读取
- **内存缓存**：`suite_ticket` 和 `suite_access_token` 应改用 Redis（多实例场景）
- **同步阻塞**：`get_permanent_code` 使用线程异步执行，应改用 Celery 或云函数
- **缺少索引**：MongoDB 集合未创建索引（如 `counters.id`、`corp_auth.corp_id`）
- **日志系统**：使用 `print()` 而非标准日志库（应改用 `logging`）