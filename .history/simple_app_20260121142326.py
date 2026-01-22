from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, Flask!'

@app.route('/api/count')
def get_count():
    return jsonify({'code': 0, 'data': 42})

@app.route('/wxwork/send_message', methods=['POST'])
def send_message():
    return jsonify({'code': 0, 'message': '消息发送成功（测试模式）'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)