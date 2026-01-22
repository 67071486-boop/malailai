from wxcloudrun.dao import db

# 插入一条测试数据到 test_collection
result = db.test_collection.insert_one({"msg": "hello, wecom-development!", "ok": True})
print("插入成功，ID：", result.inserted_id)
