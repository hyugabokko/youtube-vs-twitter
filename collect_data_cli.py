
import os, time, datetime
from dotenv import load_dotenv
from fire import Fire

from collect_live_chat_messages import collect_live_chat_messages
from collect_tweets import collect_tweets

load_dotenv(".env")
YOUTUBE_DATA_API_KEY        = os.environ.get("YOUTUBE_DATA_API_KEY")
TWITTER_CONSUMER_API_KEY    = os.environ.get("TWITTER_CONSUMER_API_KEY")
TWITTER_CONSUMER_API_SECRET = os.environ.get("TWITTER_CONSUMER_API_SECRET")
TWITTER_ACCESS_TOKEN        = os.environ.get("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

def main(channel_id=None, tags=None):
    """
    指定されたチャンネルIDのライブ配信のライブチャットとツイートを収集する．\n
    ライブ配信中のチャンネルが指定された場合は，即収集を開始し，\n
    ライブ配信中ではない場合は，最も早いライブ配信予定の開始時刻まで待機する．
    - chennel_id\n
        収集対象のライブを配信するYouTubeチャンネルのID
    - tags\n
        収集対象のツイートに付与されているタグ
    """

    # プロセスの生成
    started_datetime, finished_datetime = collect_live_chat_messages(channel_id, YOUTUBE_DATA_API_KEY)
    
    # デバッグ用のツイート収集時間指定
    # started_datetime = datetime.datetime.now(datetime.timezone.utc)
    # started_datetime = datetime.datetime(2020, 3, 7, 6, tzinfo=datetime.timezone.utc)
    # finished_datetime = started_datetime + datetime.timedelta(hours=1)
    # print(started_datetime, finished_datetime)
    # exit(0)

    collect_tweets(tags, started_datetime, finished_datetime,
        TWITTER_CONSUMER_API_KEY, TWITTER_CONSUMER_API_SECRET,
        TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)

if __name__ == "__main__":
    Fire(main)
