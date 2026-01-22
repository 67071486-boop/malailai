import sys

sys.path.append(".")

try:
    from wxcloudrun import app

    print("应用导入成功")
    print("应用配置:", app.config.get("DEBUG", "Not set"))
except Exception as e:
    print("导入错误:", e)
    import traceback

    traceback.print_exc()
