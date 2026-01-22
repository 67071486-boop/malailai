import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 是否开启debug模式
DEBUG = True

# 读取数据库环境变量

# MongoDB 连接字符串（可通过环境变量覆盖）
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb://root:Ghh15377167407@dds-bp1fe7f6fab92cf41198-pub.mongodb.rds.aliyuncs.com:3717,dds-bp1fe7f6fab92cf42736-pub.mongodb.rds.aliyuncs.com:3717/admin?replicaSet=mgset-97621859",
)
