import urllib.request
import urllib.error

try:
    response = urllib.request.urlopen("http://localhost:5000/api/count")
    print("成功连接到Flask应用")
    print("响应内容:", response.read().decode())
except urllib.error.URLError as e:
    print("连接失败:", e)
except Exception as e:
    print("其他错误:", e)
