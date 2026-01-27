from flask import render_template
from run import app


@app.route("/")
def index():
    """
    :return: 返回index页面
    """
    return render_template("index.html")

@app.route("/media/test", methods=["GET"])
def media_test_page():
    """简单的素材上传/下载测试页面。"""
    return render_template("media_test.html")


@app.route('/kf/test')
def kf_test():
    return render_template('kf_test.html')
