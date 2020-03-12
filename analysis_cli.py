
import pickle, json, datetime, math, re
import matplotlib.pyplot as plt
import japanize_matplotlib

from os import path
from fire import Fire
from tqdm import tqdm
from dateutil import parser as datetime_parser

def main(live_chat_data_path, tweet_data_path):
    """
    collect_data_cli.pyで収集したデータをもとに分析結果を出力する．
    - live_chat_data_path
        収集したライブチャットを保存したファイルパス
    - tweet_data_path
        収集したツイートを保存したファイルパス
    """

    # ライブチャットの読み込み
    live_chat_messages = []
    with open(live_chat_data_path, "rb") as file:
        live_chat_messages = pickle.load(file)
    
    # snippet.publishedAtをdatetime型にパースする
    for i in range(len(live_chat_messages)):
        live_chat_messages[i]["snippet"]["publishedAt"] = datetime_parser.parse(live_chat_messages[i]["snippet"]["publishedAt"])

    live_chat_messages.sort(key=
        lambda live_chat_message: live_chat_message["snippet"]["publishedAt"])

    # ツイートの読み込み
    tweets = []
    with open(tweet_data_path, "rb") as file:
        tweets = [status._json for status in pickle.load(file)]

    # created_atをdatetime型にパースする
    for i in range(len(tweets)):
        tweets[i]["created_at"] = datetime_parser.parse(tweets[i]["created_at"])

    tweets.sort(key=lambda tweet: tweet["created_at"])
    
    # リツイートの除外
    tweets = [tweet for tweet in tweets if not "retweeted_status" in tweet]

    # 全体の投稿数の比較
    print("投稿数")
    print("liveChatMessages:\t", len(live_chat_messages))
    print("tweets:\t\t\t", len(tweets))
    
    # 15秒あたりの投稿数の取得

    # 開始時刻と終了時刻の決定
    started_datetime = min(
        live_chat_messages[0]["snippet"]["publishedAt"],
        tweets[0]["created_at"])
    finished_datetime = max(
        live_chat_messages[-1]["snippet"]["publishedAt"],
        tweets[-1]["created_at"])

    # ライブチャットの15秒間あたりの投稿数
    live_chat_messages_per_fifteen_seconds = get_posts_nums_in_seconds(
        [live_chat_message["snippet"]["publishedAt"] for live_chat_message in live_chat_messages],
        started_datetime, finished_datetime, 15)

    # ツイートの15秒間あたりの投稿数
    seconds = 15
    tweets_per_fifteen_seconds = get_posts_nums_in_seconds(
        [tweet["created_at"] for tweet in tweets],
        started_datetime, finished_datetime, seconds)

    # グラフの初期化
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()

    # ライブチャット数のプロット
    ax1.plot(range(len(live_chat_messages_per_fifteen_seconds)),
        live_chat_messages_per_fifteen_seconds, label="ライブチャット数", color="crimson")
    ax1.set_ylabel("ライブチャット数[件]")
    
    # ツイート数のプロット
    ax2.plot(range(len(tweets_per_fifteen_seconds)),
        tweets_per_fifteen_seconds, label="ツイート数", color="deepskyblue")
    ax2.set_ylabel("ツイート数[件]")

    # 共通X軸のラベル（時刻）設定
    data_points_num = math.ceil((finished_datetime - started_datetime).seconds / seconds) + 1
    ax1.set_xticks(range(0, len(live_chat_messages_per_fifteen_seconds), 20))
    tick_label = [(started_datetime + datetime.timedelta(seconds=seconds * i)).strftime("%Y/%m/%d %H:%M:%S")
            for i in range(data_points_num)]
    ax1.set_xticklabels(tick_label[::20], rotation=20)
    
    # 凡例の表示
    handler1, label1 = ax1.get_legend_handles_labels()
    handler2, label2 = ax2.get_legend_handles_labels()
    ax1.legend(handler1 + handler2, label1 + label2, loc="upper right")
    
    # その他グラフの設定
    plt.title("15秒あたりの投稿数")
    plt.subplots_adjust(bottom=0.2)

    # グラフの出力
    plt.savefig("posts_num_series.png")
    # plt.show()

    # ユーザごとのコメント数を取得
    live_chat_messages_nums_by_user = get_posts_nums_by_user(
        [live_chat_message["snippet"]["authorChannelId"] for live_chat_message in live_chat_messages])
    tweets_nums_by_user = get_posts_nums_by_user(
        [tweet["user"]["id_str"] for tweet in tweets])
    
    # コメント数ごとのユーザ数に変換
    users_nums_by_live_chat_messages_num = get_users_nums_by_posts_num(live_chat_messages_nums_by_user)
    users_nums_by_tweets_num = get_users_nums_by_posts_num(tweets_nums_by_user)

    # コメント数ごとのユーザ数の分布をプロット

    # YouTubeの場合
    plt.figure()
    plt.bar(range(1, len(users_nums_by_live_chat_messages_num) + 1),
        users_nums_by_live_chat_messages_num, color="crimson")
    plt.xlim(left=0)
    plt.xticks([1, *range(10, len(users_nums_by_live_chat_messages_num) + 1, 10)])
    plt.title("コメント数ごとのユーザ数の分布")
    plt.xlabel("コメント数[件]")
    plt.ylabel("ユーザ数[人]")
    plt.savefig("users_dist_by_posts_num_in_twitter.png")
    # plt.show()

    # Twitterの場合
    plt.figure()
    plt.bar(range(1, len(users_nums_by_tweets_num) + 1),
        users_nums_by_tweets_num, color="deepskyblue")
    plt.xlim(left=0)
    plt.xticks([1, *range(5, len(users_nums_by_tweets_num) + 1, 5)])
    plt.title("コメント数ごとのユーザ数の分布")
    plt.xlabel("コメント数[件]")
    plt.ylabel("ユーザ数[人]")
    plt.savefig("users_dist_by_posts_num_in_youtube.png")
    
    # プロットしたグラフの表示
    plt.show()

    # ライブチャットの単語頻度分析

    # テキストの抽出
    texts = []
    texts += [live_chat_message["snippet"]["textMessageDetails"]["messageText"]
        for live_chat_message in live_chat_messages
            if live_chat_message["snippet"]["type"] == "textMessageEvent"]
    texts += [live_chat_message["snippet"]["superChatDetails"]["userComment"]
        for live_chat_message in live_chat_messages
            if live_chat_message["snippet"]["type"] == "superChatEvent"
                and "userComment" in live_chat_message["snippet"]["superChatDetails"]]
    
    # 単語頻度の取得
    live_chat_messages_word_freqs = get_word_freqs(texts)
    live_chat_messages_word_freqs = sorted(live_chat_messages_word_freqs.items(),
        key=lambda word_freq_items: word_freq_items[1]["count"], reverse=True)
    
    # 上位20件の表示
    print("\nYouTube word_freq:")
    for normalized_token, word_freq in live_chat_messages_word_freqs[:20]:
        print(normalized_token, word_freq["count"], word_freq["raws"][0].part_of_speech()[0])
    
    # ツイートの単語頻度分析

    # クエリキーワードをツイートテキストから除外するための準備

    # タグの抽出
    dir = path.dirname(tweet_data_path)
    tags = []
    while not dir.find("#") == -1:
        i = dir.find("#")
        tag = dir[i:dir.find("_")]
        tags.append(tag)
        dir = dir.replace(tag, "")
    # print(tags)
    # exit(0)
    
    # 形態素解析器の生成
    tokenizer_obj = dictionary.Dictionary().create()
    mode = tokenizer.Tokenizer.SplitMode.C

    # ツイートのテキストから除外する単語を決定
    exclude_words = []
    for tag in tags:
        tokens = tokenizer_obj.tokenize(tag, mode)
        for token in tokens:
            exclude_words.append(token.surface())

    # テキストの抽出
    texts = []
    for tweet in tweets:
        text = tweet["text"]

        # クエリキーワードをツイートテキストから除外
        for exclude_word in exclude_words:
            text = text.replace(exclude_word, "")

        texts.append(text)

    # 単語頻度の取得
    tweets_word_freqs = get_word_freqs(texts)
    tweets_word_freqs = sorted(tweets_word_freqs.items(), key=lambda word_freq_items: word_freq_items[1]["count"], reverse=True)

    # 上位20件の表示
    print("\nTwitter word_freq:")
    for normalized_token, word_freq in tweets_word_freqs[:20]:
        print(normalized_token, word_freq["count"], word_freq["raws"][0].part_of_speech()[0])

def get_users_nums_by_posts_num(posts_nums_by_user):
    """
    投稿数ごとのユーザ数の取得．
    - posts_nums
        ユーザ毎の投稿数の辞書（keyがユーザの識別子で，valueが投稿数）．
    - return
        投稿数ごとのユーザ数のリスト．
        リストのインデックス + 1が投稿数に対応している．
    """
    
    users_nums_by_posts_num = [0 for i in range(max(posts_nums_by_user.values()))]
    for posts_num in posts_nums_by_user.values():
        users_nums_by_posts_num[posts_num - 1] += 1
        
    return users_nums_by_posts_num

def get_posts_nums_by_user(users):
    """
    ユーザ毎の投稿数の取得．
    - users
        投稿したユーザのリスト
    - return
        {
            <user_id1>: <投稿数>,
            <user_id2>: <投稿数>,
            ...
        }
    """

    posts_nums_by_user = {}
    for user in users:
        if user in posts_nums_by_user:
            # 初回以降の投稿をカウント
            posts_nums_by_user[user] += 1
        else:
            # 初回の投稿をカウント
            posts_nums_by_user[user] = 1
    
    return posts_nums_by_user

def get_posts_nums_in_seconds(timestamps, started_datetime, finished_datetime, seconds):
    """
    開始時刻から終了時刻までに，一定時間ごとに投稿された件数を取得する．
    - timestamps
        投稿時刻のリスト
    - started_datetime, finished_datetime
        集計の開始時刻と終了時刻
    - seconds
        時間間隔
    - return
        開始時刻から終了時刻までを指定された時間間隔で分割した際の，
        各区間内での投稿数のリストを返す．
    """

    # データポイント数．0秒以下の差分を考慮して+1する
    data_points_num = math.ceil((finished_datetime - started_datetime).seconds / seconds) + 1
    posts_nums = [0 for i in range(data_points_num)] # 一定時間ごとの投稿数

    i = 0
    t1 = started_datetime
    t2 = t1 + datetime.timedelta(seconds=seconds)
    for timestamp in timestamps:
        if t1 <= timestamp < t2:
            # 投稿時刻がt2より小さい場合
            posts_nums[i] += 1
        else:
            # 投稿時刻がt2以上の場合
            i += 1
            posts_nums[i] += 1
            
            # 集計する範囲の更新
            t1 = t2
            t2 = t1 + datetime.timedelta(seconds=seconds)
    
    return posts_nums

from sudachipy import config, tokenizer, dictionary

def get_word_freqs(texts):
    """
    文字列のリストを入力すると，すべての文字列に対して形態素解析を行い，
    正規化された単語の出現回数と，形態素解析の結果を辞書型で返す．
    無視される品詞：補助記号，空白，助動詞，助詞，代名詞，接頭辞，接尾辞
    - return
        {
            <正規化された単語>: {
                "count": <出現回数>,
                "raws": [<token>, <token>, ...]
            }
        }
    """

    # URLの除外
    texts = [re.sub(r'(http|https)://([-\w]+\.)+[-\w]+(/[-\w./?%&=]*)?', "", text) for text in texts]

    word_freqs = {}

    # 形態素解析器の生成
    tokenizer_obj = dictionary.Dictionary().create()
    mode = tokenizer.Tokenizer.SplitMode.C

    print("\ntokenizing ...")
    for text in tqdm(texts):
        tokens = tokenizer_obj.tokenize(text, mode)
        for token in tokens:
            # 特定の品詞をスキップする
            pos = token.part_of_speech()[0]
            if pos in ["補助記号", "空白", "助動詞", "助詞", "代名詞", "接頭辞", "接尾辞"]:
                continue

            normalized_token = token.normalized_form()
            if normalized_token in word_freqs:
                # 既出の単語をカウント
                word_freqs[normalized_token]["count"] += 1
                word_freqs[normalized_token]["raws"] += [token]
            else:
                # 初登場の単語をカウント
                word_freqs[normalized_token] = {}
                word_freqs[normalized_token]["count"] = 1
                word_freqs[normalized_token]["raws"] = [token]

    return word_freqs

if __name__ == "__main__":
    Fire(main)