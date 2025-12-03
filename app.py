from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os 
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

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

# --- データ分析機能（最終版：二次回帰分析による予測ロジック） ---
@app.route('/analyze')
def analyze_events():
    query = db.session.query(Event)
    df = pd.read_sql(query.statement, db.engine)
    
    analysis_data = {'total_events': 0, 'regression_result': '分析データ不足'}
    count_data_table = "<p>データがありません。</p>"
    display_data = "<p>分析できるデータがありません。</p>"
    
    # 回帰分析には最低3つのデータが必要
    if not df.empty and len(df) >= 3: 
        
        # 1. データのクレンジングと特徴量生成
        df['start_dt'] = pd.to_datetime(df['date'] + ' ' + df['start_time'])
        df['end_dt'] = pd.to_datetime(df['date'] + ' ' + df['end_time'])
        # 予定の実行時間（分）を計算
        df['duration_min'] = (df['end_dt'] - df['start_dt']).dt.total_seconds() / 60
        
        # 実行時間が0のデータを除外
        clean_df = df[df['duration_min'] > 0]
        
        if len(clean_df) >= 3:
            # 1. 特徴量エンジニアリング：二次特徴量（X^2）を追加
            X_linear = clean_df['duration_min'].values.reshape(-1, 1) # X (実行時間)
            X_squared = X_linear ** 2 # X^2 (実行時間の二乗)
            
            # XとX^2を結合して、新しい説明変数X_polyを作成
            X_poly = np.hstack((X_linear, X_squared))

            Y = clean_df['satisfaction'].values   # 目的変数 (満足度)
            
            # 2. 線形回帰モデルの構築と学習 (XとX^2の項を持つため、二次モデルを表現できる)
            model = LinearRegression()
            model.fit(X_poly, Y)
            
            # 3. 分析結果の抽出
            # X^2の係数 (a) と Xの係数 (b) を取得
            coefficient_X2 = round(model.coef_[1], 5) # X^2の係数 (a)
            coefficient_X = round(model.coef_[0], 3) # Xの係数 (b)
            r_squared = round(model.score(X_poly, Y), 3)

            # 結果に基づくメッセージ生成 (X^2の係数が負であれば、最適な点が存在する非線形関係)
            if coefficient_X2 < -0.00001: 
                # **【最適な実行時間の計算を追記】**
                # Optimal Time (分) = -b / (2a)
                optimal_time_min = round(-coefficient_X / (2 * coefficient_X2))
                
                # 結果メッセージを更新
                correlation_text = f"""実行時間と満足度の間に**上に凸の二次曲線的な非線形な相関**が見られます。
最適な実行時間（満足度を最大にする時間）は **{optimal_time_min} 分** です。"""
            
            else:
                optimal_time_min = "算出不能"
                correlation_text = "二次モデルを適用しましたが、非線形な相関は確認できませんでした。"
            
            regression_result_message = f"""
            **【二次回帰分析の結果】**
            予測モデル: 満足度 = ({coefficient_X2}) X² + ({coefficient_X}) X + (切片)
            決定係数 (R-squared): {r_squared}
            結果: {correlation_text}
            """
            
            analysis_data['regression_result'] = regression_result_message
            analysis_data['total_events'] = len(df)
            
        else:
            analysis_data['regression_result'] = "データ不足：実行時間が0でないデータが3件未満です。"
            analysis_data['total_events'] = len(df)


        # 概要情報 (タイトル別件数) は残しておく
        title_counts = df['title'].value_counts().reset_index()
        title_counts.columns = ['予定のタイトル', '件数']
        count_data_table = title_counts.to_html(classes='data', index=False)
        
        display_data = df.tail(5)[['title', 'date', 'start_time', 'end_time', 'satisfaction', 'duration_min']].to_html(classes='data', index=False)
    
    else:
        analysis_data['regression_result'] = f"データ不足：回帰分析には最低3件のデータが必要です。現在 {len(df)} 件です。"
        analysis_data['total_events'] = len(df)

    return render_template('analyze.html', 
                           analysis=analysis_data, 
                           data_table=display_data, 
                           count_data_table=count_data_table
                          )

# --- サーバー起動部分（変更なし） ---
if __name__ == '__main__':
    with app.app_context():
        # db.create_all() は、site.dbがまだ存在しない場合に実行されます
        db.create_all() 
    app.run(debug=True)