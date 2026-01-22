import sys
sys.path.append('.')

from wxcloudrun import app

if __name__ == '__main__':
    print("正在启动Flask应用...")
    print(f"调试模式: {app.config.get('DEBUG', False)}")
    print(f"数据库URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')}")

    try:
        app.run(host='127.0.0.1', port=5000, debug=True)
    except Exception as e:
        print(f"启动错误: {e}")
        import traceback
        traceback.print_exc()