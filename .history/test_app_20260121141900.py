from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/test')
def test():
    return {'message': 'Flask is working!', 'status': 'success'}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)