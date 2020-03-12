
import json, pickle
from os import path

from dateutil import parser
from fire import Fire

def main(live_chat_messages_fpath=None, tweets_fpath=None):
    if not live_chat_messages_fpath == None:
        # 収集したデータを保存したファイルのディレクトリ名と拡張子なしのファイル名の取得
        live_chat_messages_dir = path.dirname(live_chat_messages_fpath)
        live_chat_messages_fname = path.splitext(path.basename(live_chat_messages_fpath))[0]

        # liveChatMessages
        # データの読み込み
        live_chat_messages = []
        with open(live_chat_messages_fpath, "rb") as file:
            live_chat_messages = pickle.load(file)

        # 時系列順に並び替え
        live_chat_messages.sort(key=
            lambda live_chat_message: parser.parse(live_chat_message["snippet"]["publishedAt"]))

        # jsonファイルに書き出し
        with open(path.join(live_chat_messages_dir, live_chat_messages_fname + ".json"), "w", encoding="utf8") as file:
            json.dump(live_chat_messages, file, indent=2, ensure_ascii=False)

    if not tweets_fpath == None:
        # 収集したデータを保存したファイルのディレクトリ名と拡張子なしのファイル名の取得
        tweets_dir = path.dirname(tweets_fpath)
        tweets_fname = path.splitext(path.basename(tweets_fpath))[0]

        # データの読み込み
        tweets = []
        with open(tweets_fpath, "rb") as file:
            tweets = [status._json for status in pickle.load(file)]
        
        # 時系列順に並び替え
        tweets.sort(key=
            lambda tweet: parser.parse(tweet["created_at"]))
        # print(tweets[0])

        # jsonファイルに書き出し
        with open(path.join(tweets_dir, tweets_fname + ".json"), "w", encoding="utf8") as file:
            json.dump(tweets, file, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    Fire(main)
