from wxcloudrun.dao import client

try:
    info = client.server_info()
    print("MongoDB 连接成功！")
    print(info)
except Exception as e:
    print("MongoDB 连接失败：", e)
