# GT7 テレメトリーデータ可視化

グランツーリスモ7のテレメトリーデータを可視化・比較するためのStreamlitベースのWEBアプリケーション

## 主な機能

- ユーザー認証システム（サインアップ・ログイン機能）
- Firebase上のデータを可視化
- レース比較ツール
- コーストラック表示
- ラップタイム分析
- ユーザー毎のテレメトリ比較：
  - 速度、RPM、アクセル、ブレーキデータ
  - エンジンパラメータ（油圧、燃料、ブースト）
  - 車両ダイナミクス（サスペンション、タイヤ温度）
  - 位置・回転データ

## 必要条件

- Python 3.8以上

## インストール

1. リポジトリのクローン
2. 依存関係のインストール：
```bash
pip install -r requirements.txt
```

3. 環境変数の設定：
`.env`ファイルに以下のFirebase認証情報を設定：（現状すでに設定済）
```
FIREBASE_TYPE=
FIREBASE_PROJECT_ID=
FIREBASE_PRIVATE_KEY_ID=
FIREBASE_PRIVATE_KEY=
FIREBASE_CLIENT_EMAIL=
FIREBASE_CLIENT_ID=
FIREBASE_AUTH_URI=
FIREBASE_TOKEN_URI=
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=
FIREBASE_CLIENT_X509_CERT_URL=
FIREBASE_UNIVERSE_DOMAIN=
```

4. ユーザー認証設定：

a. `userdata.csv`の編集：
```csv
id,name,password,email
username1,Display Name1,password1,email1@example.com
username2,Display Name2,password2,email2@example.com
taroyamada01,Yamada Taro , thisismypassword,email3@example.com

```

b. 認証設定の生成：
```bash
python create_yaml.py
```
→config.yamlが作成され、mainにpushすると自動でstreamlit側に更新が反映される

## プロジェクト構成

- `streamlit_app.py`: メインアプリケーション
- `visualization.py`: データ可視化機能
- `track_vis.py`: コーストラック可視化機能
- `create_yaml.py`: ユーザー認証設定生成
- `config.yaml`: ユーザー認証情報設定ファイル（create_yaml.pyによって作成される）
- `userdata.csv`: ユーザーデータ設定ファイル（手入力）
- `course_track/`: コーストラックJSONファイル格納ディレクトリ

## ローカル使用方法

1. Streamlitサーバーの起動：
```bash
streamlit run streamlit_app.py
```

2. ブラウザでアプリケーションにアクセス（デフォルト：http://localhost:8501）

3. アカウント作成またはログイン（userdata.csvの情報）

4. レースデータ比較：
   - ユーザー名を入力してレースを検索
   - 分析するレースを選択
   - 比較するラップを選択
   - インタラクティブな可視化とメトリクスを表示

## ユーザー管理
- Streamlit-Authenticatorによるユーザー管理