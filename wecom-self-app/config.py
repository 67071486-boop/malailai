import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 是否开启debug模式（从环境变量读取，默认 False）
DEBUG = os.environ.get("DEBUG", "false").strip().lower() in {"1", "true", "yes", "y", "on"}

# MongoDB 数据库（可通过环境变量覆盖）
MONGO_URI: str = os.environ.get(
    "MONGO_URI",
    "mongodb://root:",
)
MONGO_DB_NAME: str = os.environ.get("MONGO_DB_NAME", "demo")

# 企业微信自建应用（企业内部开发）
WXWORK_CORP_ID: str = os.environ.get("WXWORK_CORP_ID", "")
# 应用 AgentId，网页授权 snsapi_privateinfo / snsapi_userinfo 时必填
WXWORK_AGENT_ID: str = os.environ.get("WXWORK_AGENT_ID", "")
# 应用 Secret（在管理后台「应用管理 - 自建应用」中获取，用于 gettoken）
WXWORK_AGENT_SECRET: str = os.environ.get("WXWORK_AGENT_SECRET", "")
# 回调 URL 配置的 Token 与 EncodingAESKey
WXWORK_TOKEN: str = os.environ.get("WXWORK_TOKEN", "")
WXWORK_ENCODING_AES_KEY: str = os.environ.get("WXWORK_ENCODING_AES_KEY", "")
# 网页授权完成后的前端回调地址（可信域名内）
WXWORK_OAUTH_REDIRECT: str | None = os.environ.get("WXWORK_OAUTH_REDIRECT")
