from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os 

# --- データベース設定（変更なし） ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# -----------------------------------

# 予定のデータ構造（変更なし）
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f"Event('{self.title}', '{self.date}')"

# --- トップページ（修正） ---
@app.route('/')
def index():
    # データベースから全ての予定（Event）を取得し、日付順に並べ替える
    events = Event.query.order_by(Event.date).all()
    
    # 取得したデータを index_list.html に渡して表示
    # ここで index_list.html をレンダリング（表示）します。
    return render_template('index_list.html', events=events)

# --- 予定の作成機能（CRUDの Create） ---
@app.route('/create', methods=['GET', 'POST'])
def create_event():
    # フォームからデータが送信された場合
    if request.method == 'POST':
        # フォームからデータを取得
        event_title = request.form['title']
        event_date = request.form['date']
        event_description = request.form['description']
        
        # データベースに保存するための新しいEventオブジェクトを作成
        new_event = Event(title=event_title, date=event_date, description=event_description)
        
        try:
            db.session.add(new_event) # データベースに追加
            db.session.commit()       # 変更を確定
            return redirect(url_for('index')) # トップページに戻る
        except:
            # エラーが発生した場合（デバッグ用）
            return '予定の保存中にエラーが発生しました'

    # ただページにアクセスした場合（フォームを表示）
    return render_template('create.html')

# --- 予定の詳細表示・編集機能（CRUDの Read/Update） ---
@app.route('/detail/<int:id>')
def detail_event(id):
    # IDに基づいて予定をデータベースから取得する。なければ404エラー
    event = Event.query.get_or_404(id)
    return render_template('detail.html', event=event)


# --- 予定の更新機能（CRUDの Update） ---
@app.route('/update/<int:id>', methods=['POST'])
def update_event(id):
    # IDに基づいて予定を取得
    event = Event.query.get_or_404(id)
    
    # フォームから送られた新しいデータを取得
    event.title = request.form['title']
    event.date = request.form['date']
    event.description = request.form['description']

    try:
        db.session.commit() # 変更を確定
        return redirect(url_for('index')) # トップページに戻る
    except:
        return '予定の更新中にエラーが発生しました'


# --- 予定の削除機能（CRUDの Delete） ---
@app.route('/delete/<int:id>', methods=['POST'])
def delete_event(id):
    # IDに基づいて予定を取得
    event = Event.query.get_or_404(id)
    
    try:
        db.session.delete(event) # データベースから削除
        db.session.commit()      # 変更を確定
        return redirect(url_for('index')) # トップページに戻る
    except:
        return '予定の削除中にエラーが発生しました'

# --- サーバー起動部分（変更なし） ---
if __name__ == '__main__':
    with app.app_context():
        # db.create_all() は、site.dbがまだ存在しない場合に実行されます
        db.create_all() 
    app.run(debug=True)