import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 是否开启debug模式
DEBUG = False

# MongoDB 数据库（可通过环境变量覆盖）
MONGO_URI: str = os.environ.get(
	"MONGO_URI",
	"mongodb://root:",
)
MONGO_DB_NAME: str = os.environ.get("MONGO_DB_NAME", "demo")

# 企业微信相关配置（统一从此处读取）
WXWORK_CORP_ID: str = os.environ.get("WXWORK_CORP_ID", "your_corp_id")
WXWORK_PROVIDER_SECRET: str = os.environ.get("WXWORK_PROVIDER_SECRET", "your_provider_secret")
# 第三方应用配置
WXWORK_TOKEN: str = os.environ.get("WXWORK_TOKEN", "your_token")
WXWORK_ENCODING_AES_KEY: str = os.environ.get("WXWORK_ENCODING_AES_KEY", "your_aes_key")
WXWORK_SUITE_ID: str = os.environ.get("WXWORK_SUITE_ID", "your_suite_id")
WXWORK_SUITE_SECRET: str = os.environ.get("WXWORK_SUITE_SECRET", "your_suite_secret")
WXWORK_OAUTH_REDIRECT: str | None = os.environ.get("WXWORK_OAUTH_REDIRECT")
