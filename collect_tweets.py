
from time import sleep
import os, sys, datetime, re
from dateutil import parser
from copy import deepcopy

import tweepy

from Save import Save

def collect_tweets(tags, youtube_live_started_datetime, youtube_live_finished_datetime,
    consumer_key, consumer_secret, access_token, access_token_secret):
    """
    YouTubeのライブ配信開始時刻から終了時刻までの間，ツイートを収集し保存する．\n
    終了時刻は，現在時刻よりも過去である必要がある．
    """

    if type(youtube_live_started_datetime) is str:
        youtube_live_started_datetime = parser.parse(youtube_live_started_datetime)
    if type(youtube_live_finished_datetime) is str:
        youtube_live_finished_datetime = parser.parse(youtube_live_finished_datetime)

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

    # クエリの生成
    q = tags.replace(",", " OR ")
    print("query:", q)

    # データ保存準備
    save_dir = q + "_" + str(youtube_live_started_datetime) + "_" + str(youtube_live_finished_datetime)
    save_dir = os.path.join("tweets", re.sub(r'[\\|/|:|?|.|"|<|>|\|]', "_", save_dir))
    save = Save(save_dir)

    first_tweet = None  # ライブ配信開始後最初のツイート
    last_tweet = None   # ライブ配信終了前最後のツイート

    # ライブ配信終了前最後のツイートを取得する
    max_id = None   # max_idより以前のツイートを取得する
    while last_tweet == None:
        # ツイートの取得
        if max_id == None:
            # 初回
            tweets = api.search(q, result_type="recent", count=100)
        else:
            # 初回以降
            tweets = api.search(q, result_type="recent", count=100, max_id=max_id)

        # ループすることでツイートをさかのぼる
        for tweet in tweets:
            tweet.created_at = set_utc(tweet.created_at)
            if tweet.created_at < youtube_live_finished_datetime:
                # ライブ配信終了前際のツイートを取得
                last_tweet = tweet

                # ここで取得したlast_tweet以前のすべてのツイートをダンプファイルに保存
                # ただし，ライブ配信開始後のツイートの限る
                save.dump([tweet for tweet in tweets
                    if youtube_live_started_datetime < set_utc(tweet.created_at) < youtube_live_finished_datetime])

                break
            # print(tweet.created_at)
        
        # 取得できたツイートが1つ以上の場合
        if len(tweets) > 0:
            max_id = tweets[-1].id_str  # 取得したツイートの中で最も古いツイートのid
        sleep(2)
        # exit(0)
    print("last_tweet:", last_tweet.created_at, last_tweet.id)

    # ライブ配信開始後最初のツイートまでをダンプファイルに保存する
    max_id = None   # max_idより以前のツイートを取得する
    while first_tweet == None:
        # ツイートの取得
        if max_id == None:
            # 初回
            tweets = api.search(q, result_type="recent", count=100, max_id=last_tweet.id_str)
        else:
            # 初回以降
            tweets = api.search(q, result_type="recent", count=100, max_id=max_id)

        # ループすることでツイートをさかのぼる
        for i, tweet in enumerate(tweets):
            tweet.created_at = set_utc(tweet.created_at)
            if tweet.created_at < youtube_live_started_datetime:
                first_tweet = tweets[i - 1] # ライブ配信開始後最初のツイートを取得
                save.dump([tweet for tweet in tweets
                    if youtube_live_started_datetime < set_utc(tweet.created_at) < youtube_live_finished_datetime])
                break
        
        max_id = tweets[-1].id_str  # 取得したツイートの中で最も古いツイートのid
        
        if first_tweet == None:
            # 取得したすべてのツイートをダンプファイルに保存
            # この条件を満たすなら，すべてのツイートが収集範囲に入っていることが保証されている
            save.dump(tweets)
            for tweet in tweets:
                print(tweet.created_at, tweet.text)
        sleep(2)

    print("first_tweet:", first_tweet.created_at, first_tweet.id)

    # ダンプファイルの保存
    save.store("tweets")

def set_utc(tweet_datetime):
    """
    引数で与えられたタイムゾーン設定のないdatetimeにUTCのタイムゾーン設定を付与する．
    """
    _tweet_datetime = deepcopy(tweet_datetime)
    _tweet_datetime += datetime.timedelta(hours=9)
    return _tweet_datetime.astimezone(datetime.timezone.utc)
