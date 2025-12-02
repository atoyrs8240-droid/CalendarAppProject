from flask import Flask

# Flaskアプリを初期化
app = Flask(__name__)

# '/' (トップページ) にアクセスしたときに実行される関数
@app.route('/')
def hello_world():
    return 'Hello, Flask! これはカレンダーアプリのサーバーです'

# このファイルが直接実行された場合にアプリを起動
if __name__ == '__main__':
    app.run(debug=True)