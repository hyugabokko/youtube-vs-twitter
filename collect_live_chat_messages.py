
from time import sleep
import os, glob, pickle, shutil, datetime, re

from YouTubeAPI import YouTubeAPI

def collect_live_chat_messages(channel_id, youtube_data_api_key):
    """
    指定されたチャンネルでライブ配信が開始されるまで待機し，\n
    ライブ配信開始から終了までの間のチャットメッセージをpickleでファイルに保存する．
    """

    api = YouTubeAPI(youtube_data_api_key, channel_id)

    # videoIdの取得，ライブ配信のvideoIdが取得できるまで待機
    print("waiting for live broadcast ...")

    # ライブ配信中のvideoIdを取得
    video_id = api.get_live_video()
    scheduled_start_time = None
    live_chat_id = None
    live_title = None

    if video_id == None:
        # ライブ配信中ではない場合，ライブ配信予定のvideoIdとライブ配信開始時刻を取得
        video_id, live_title, scheduled_start_time, live_chat_id = api.get_upcoming_video()
    
    if video_id == None:
        print("指定されたチャンネル上にライブ配信，または，ライブ配信予定がありません．")
        return None, None

    if live_chat_id == None:
        # ライブ配信中の場合，liveChatIdを取得
        live_title, live_chat_id = api.get_live(video_id)

    # ライブ配信中ではない場合，ライブ配信開始まで待機
    print("live broadcast title: " + live_title)
    if not scheduled_start_time == None:
        current_time = datetime.datetime.now(datetime.timezone.utc)
        sleep((scheduled_start_time - current_time).seconds)
        # exit(0)

    # liveChatMessagesの取得
    live_chat_messages_dump = []
    
    # 初回呼び出し(pageTokenを指定しない)
    live_started_datetime = datetime.datetime.now(datetime.timezone.utc)
    print("start collecting liveChatMesages ({0})...".format(live_started_datetime))
    live_chat_messages_dump, polling_interval_millis, next_page_token = api.get_live_chat_messages(live_chat_id)
    for live_chat_message in live_chat_messages_dump:
        print(live_chat_message["snippet"]["publishedAt"], live_chat_message["snippet"]["displayMessage"])

    # ダンプファイルに書き出し
    dump_number = 0
    working_dir = os.path.join(channel_id, re.sub(r'[\\|/|:|?|.|"|<|>|\|]', "_", live_title))
    dump_dir = os.path.join(working_dir, "dumps")
    os.makedirs(dump_dir)
    with open(os.path.join(dump_dir, str(dump_number)), "wb") as file:
        pickle.dump(live_chat_messages_dump, file)
    dump_number += 1
    
    sleep((polling_interval_millis / 1000) * 1.5)

    # ライブ配信が終わるまでchatMessagesを取得する
    live_finished = False
    zero_messages_count = 0
    while not live_finished:
        try:
            live_chat_messages_dump, polling_interval_millis, next_page_token = api.get_live_chat_messages(live_chat_id, next_page_token)
        except:
            # ライブ配信終了判定
            live_finished = True
            break

        for live_chat_message in live_chat_messages_dump:
            print(live_chat_message["snippet"]["publishedAt"], live_chat_message["snippet"]["displayMessage"])

        # ダンプファイルに書き出し
        if not len(live_chat_messages_dump) == 0:
            with open(os.path.join(dump_dir, str(dump_number)), "wb") as file:
                pickle.dump(live_chat_messages_dump, file)
            dump_number += 1
            zero_messages_count = 0
        else:
            zero_messages_count += 1
        
        # ライブ配信終了判定
        # if zero_messages_count > 5:
        #     live_finished = True
        #     break

        try:
            sleep((polling_interval_millis / 1000) * 1.5)
        except KeyboardInterrupt:
            # TODO: ライブ終了時の挙動が知りたい
            # ライブ配信が終わったタイミングでCtrl+Cを押す
            print(live_chat_messages_dump)
            print(polling_interval_millis)
            print(next_page_token)
            break
    
    live_finished_datetime = datetime.datetime.now(datetime.timezone.utc)
    print("finidhed ({0}).".format(live_finished_datetime))

    # ダンプファイルから全liveChatMessagesを取得
    live_chat_messages = []
    for file_path in glob.glob("./" + dump_dir + "/*"):
        with open(file_path, "rb") as file:
            live_chat_messages += pickle.load(file)
    # for live_chat_message in live_chat_messages:
        # print(live_chat_message["snippet"]["publishedAt"], live_chat_message["snippet"]["displayMessage"])
    
    # 1つのファイルに格納
    with open(os.path.join(working_dir, "liveChatMessages"), "wb") as file:
        pickle.dump(live_chat_messages, file)

    shutil.rmtree(dump_dir)
    
    print("saved to " + os.path.join(working_dir, "liveChatMessages"))
    
    return live_started_datetime, live_finished_datetime
