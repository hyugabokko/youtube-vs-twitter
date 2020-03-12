
# youtube-vs-twitter

## 概要
指定されたYouTubeチャンネル上のライブ配信チャットメッセージ（以降，ライブチャット）と，ライブ配信に関連するタグが付与されたツイート（以降，ライブ関連ツイート）を収集し，
ライブチャットとライブ関連ツイートの定量的な違いを比較するツール群．

## 使い方

### 環境構築

#### パッケージインストール
```sh
pip install -r requirements.txt
```

#### 環境変数の設定
本ツールはYouTube Data APIとTwitter APIを利用するための認証情報が必要である．  
`.env_template`ファイルを`.env`にリネームし，以下の情報を入力する．
```.env
YOUTUBE_DATA_API_KEY = 
TWITTER_CONSUMER_API_KEY = 
TWITTER_CONSUMER_API_SECRET = 
TWITTER_ACCESS_TOKEN = 
TWITTER_ACCESS_TOKEN_SECRET = 
```

### collect_data_cli
データ収集を行うスクリプト．  
ライブチャットを収集したいチャンネルIDと，ライブ関連ツイートのタグ（複数入力可）を引数に入力する．  
スクリプト実行時に指定したチャンネル上ですでに配信が開始されている場合は，直ちにライブチャットの収集を開始する．
配信が開始されていない場合は，直近のライブ配信予定を取得し，開始予定時刻まで待機後，自動で収集を開始する．
ライブ配信終了後，ライブ配信開始時刻から終了時刻までのツイートを収集する．  
収集したライブチャットは`pickle`形式で`./<channel_id>/<live_title>/liveChatMessage`に保存される．
また，ツイートも同様に`pickle`形式で`./tweets/#tag1_#tag2_<started_datetime>_<finished_datetime>/tweets`に保存される．

実行コマンド例：
```sh
python collect_data_cli.py <chennel_id> "#tag1,#tag2"
```

### pickle2json_cli
データ収集後の`pickle`ファイルをJSON形式に変換するスクリプト．  
引数に`collect_data_cli.py`で収集した`pickle`形式のライブチャットデータのファイルパス，または，
ツイートデータのファイルパスを指定すれば，変換元のファイルがあるディレクトリにそれぞれ
`liveChatMessage.json`，`tweets.json`を出力する．  
このスクリプトを実行しなくても，データ分析用スクリプトの`analysis_cli.py`は実行可能である．

実行コマンド例：
```sh
python pickle2json_cli.py --live-chat-messages-fpath="./<channel_id>/<live_title>/liveChatMessage" --tweets-fpath="./tweets/#tag1_#tag2_<started_datetime>_<finished_datetime>/tweets"
```

### analysis_cli
収集したデータを用いて分析を行うためのスクリプト．
引数に`collect_data_cli.py`で収集した`pickle`形式のライブチャットデータのファイルパスと，
ツイートデータのファイルパスを指定し，ライブチャット，ツイートに対して以下を出力する．
- ライブチャット，ツイートの投稿数
- 15秒あたりの投稿数の推移(`posts_num_series.png`に出力)
- コメント数ごとのユーザ数の分布(`users_dist_by_posts_num_in_youtube.png`，`users_dist_by_posts_num_in_twitter.png`に出力)
- 出現頻度上位20件の単語(形態素)

```sh
python .\analysis_cli.py "./<channel_id>/<live_title>/liveChatMessage" "./tweets/#tag1_#tag2_<started_datetime>_<finished_datetime>/tweets"
```
