from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os 
import pandas as pd

# --- データベース設定（変更なし） ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# -----------------------------------

# 予定のデータ構造（時間と満足度カラムを追加）
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    # --- 【時間データを追加】 ---
    start_time = db.Column(db.String(10), nullable=True) # 開始時間 (例: "09:00")
    end_time = db.Column(db.String(10), nullable=True)   # 終了時間 (例: "10:00")
    # ---------------------------
    description = db.Column(db.Text, nullable=True)
    # --- 【満足度データを追加】 ---
    satisfaction = db.Column(db.Integer, default=0, nullable=True) # 0:未評価, 1-5:満足度
    # ---------------------------
    
    def __repr__(self):
        # f-stringの中身も修正が必要です
        return f"Event('{self.title}', '{self.date}', '{self.start_time}-{self.end_time}')"

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
        # --- 【ここを修正】 時間データを取得 ---
        event_start_time = request.form['start_time']
        event_end_time = request.form['end_time']
        # ------------------------------------
        event_description = request.form['description']
        
        # データベースに保存するための新しいEventオブジェクトを作成
        new_event = Event(title=event_title, date=event_date,
                          start_time=event_start_time, end_time=event_end_time, # <-- ここに追加
                          description=event_description)
        
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
    # --- 【ここを修正】 時間と満足度データを取得 ---
    event.start_time = request.form['start_time']
    event.end_time = request.form['end_time']
    event.satisfaction = request.form['satisfaction']
    # ---------------------------------------------
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

# --- データ分析機能（ESのアピールポイント） ---
@app.route('/analyze')
def analyze_events():
    # データベースから全データをPandas DataFrameとして取得
    query = db.session.query(Event)
    df = pd.read_sql(query.statement, db.engine)

    # データの処理（ESでの分析内容をここに追加します）
    if not df.empty:
        # 簡易分析結果の計算例：予定の総数を計算
        total_events = len(df)
        
        # --- ESアピール用の具体的な分析 ---
        # 1. タイトルごとの出現回数をカウント
        title_counts = df['title'].value_counts().reset_index()
        title_counts.columns = ['予定のタイトル', '件数']
        
        # 2. 最も多い予定のタイトルと件数を取得
        top_title = title_counts.iloc[0]['予定のタイトル']
        top_count = int(title_counts.iloc[0]['件数']) # intに変換
        
        # 3. 件数の多い順にソートした全件数をHTMLとして準備
        count_data_table = title_counts.to_html(classes='data', index=False)
        
        # 分析結果をテンプレートに渡す辞書
        analysis_data = {
            'total_events': total_events,
            'top_title': top_title,
            'top_count': top_count
        }
        
        # 取得したデータの一部（例: 最新5件）をHTMLテーブルにしてテンプレートに渡す
        display_data = df.tail(5).to_html(classes='data', index=False)
    else:
        analysis_data = {'total_events': 0, 'top_title': '', 'top_count': 0}
        display_data = "<p>分析できるデータがありません。</p>"
        count_data_table = "<p>データがありません。</p>"

    return render_template('analyze.html', analysis=analysis_data, data_table=display_data, count_data_table=count_data_table)

# --- サーバー起動部分（変更なし） ---
if __name__ == '__main__':
    with app.app_context():
        # db.create_all() は、site.dbがまだ存在しない場合に実行されます
        db.create_all() 
    app.run(debug=True)