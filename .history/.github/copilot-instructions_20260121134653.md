# 微信云托管 Flask 计数器服务 - AI 助手指导说明

## 架构概述
这是一个基于 Flask 的简单计数器服务，用于微信云托管，具有模块化结构：
- **wxcloudrun/**：主应用包，包含视图、DAO、模型和响应工具
- **单计数器模式**：使用 ID=1 作为全局计数器实例
- **MySQL 集成**：通过 `config.py` 进行环境变量数据库配置

## 关键模式与约定

### 数据库操作
始终使用 DAO 模式：
```python
from wxcloudrun.dao import query_counterbyid, insert_counter, update_counterbyid, delete_counterbyid
# 单计数器始终查询 ID=1
counter = query_counterbyid(1)
```

### 响应格式化
始终使用响应工具构建一致的 API 响应：
```python
from wxcloudrun.response import make_succ_response, make_err_response, make_succ_empty_response
return make_succ_response(counter.count)  # 成功响应（带数据）
return make_err_response('错误信息')  # 错误响应
return make_succ_empty_response()  # 成功响应（无数据）
```

### API 结构
- `GET /api/count`：获取当前计数（计数器不存在时返回 0）
- `POST /api/count`：使用 `{"action": "inc"}` 或 `{"action": "clear"}` 更新计数器

### 开发工作流
- **本地运行**：`python run.py <host> <port>`（例如：`python run.py 127.0.0.1 5000`）
- **数据库配置**：环境变量 `MYSQL_USERNAME`、`MYSQL_PASSWORD`、`MYSQL_ADDRESS`
- **调试模式**：在 `config.py` 中设置 `DEBUG = True` 进行开发

### 代码组织
- **views.py**：路由处理器和业务逻辑
- **dao.py**：数据库访问层
- **model.py**：SQLAlchemy 模型（Counters 表）
- **response.py**：标准化响应构建器
- **config.py**：环境和应用配置

## 重要注意事项
- 计数器在首次自增时自动创建（如果不存在）
- 清零操作会完全删除计数器记录
- 所有时间戳使用 `datetime.now()` 设置 created_at/updated_at
- 扩展路由时遵循 Flask Blueprint 模式