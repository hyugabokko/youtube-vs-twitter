
import datetime
from dateutil import parser

from googleapiclient.discovery import build

class YouTubeAPI():
    def __init__(self, api_key, channel_id):
        self.api = build("youtube", "v3", developerKey=api_key)
        self.channel_id = channel_id

    def search_videos(self, part, event_type):
        return self.api.search().list(type="video",
                channelId=self.channel_id,
                part=part, eventType=event_type
            ).execute()["items"]

    def get_live_video(self):
        """
        配信中のvideoIdを返す
        """
        video_id = None

        videos = self.search_videos("id", "live")

        if len(videos) > 0:
            video_id = videos[0]["id"]["videoId"]

        return video_id

    def __get_live_videos(self, video_id):
        """
        現在ライブ配信中，または配信予定のvideoIdを渡し，\n
        liveStreamingDetails, snippetを返す．\n
        videoIdが条件を満たさない場合は`None, None`を返す．\n
        """
        videos_result = self.api.videos().list(
                part="liveStreamingDetails,snippet",
                id=video_id
            ).execute()["items"]

        if len(videos_result) > 0:
            return videos_result[0]["liveStreamingDetails"], videos_result[0]["snippet"]
        return None, None

    def get_upcoming_video(self, video_id=None):
        """
        配信予定のvideoIdと配信予定時間を返す．\n
        配信予定が複数ある場合は，配信開始時刻が最も早い配信を返す．
        """
        scheduled_start_time = datetime.datetime(2038, 1, 9, tzinfo=datetime.timezone.utc)
        active_live_chat_id = None
        live_title = None
        
        if video_id == None:
            # video_idの指定がない場合，すべての配信予定を取得する

            videos = self.search_videos("id,snippet", "upcoming")
            if len(videos) == 0:
                return None, None
            for video in videos:
                _video_id = video["id"]["videoId"]
                live_streaming_details, snippet = self.__get_live_videos(_video_id)
                _scheduled_start_time = parser.parse(live_streaming_details["scheduledStartTime"])

                # 配信時刻が早い方を残す（配信が開始されなかった配信予定は含めない）
                if scheduled_start_time > _scheduled_start_time > datetime.datetime.now(datetime.timezone.utc):
                    scheduled_start_time = _scheduled_start_time
                    video_id = _video_id
                    active_live_chat_id = live_streaming_details["activeLiveChatId"]
                    live_title = snippet["title"]
        else:
            live_streaming_details, snippet = self.__get_live_videos(video_id)
            scheduled_start_time = parser.parse(live_streaming_details["scheduledStartTime"])
            active_live_chat_id = live_streaming_details["activeLiveChatId"]
            live_title = snippet["title"]

        return video_id, live_title, scheduled_start_time, active_live_chat_id
    
    def get_live(self, video_id):
        """
        配信中，または，配信予定のliveChatIdを返す．\n
        配信中ではない，または，配信予定がない場合は`None`を返す．
        """

        if video_id == None:
            # ライブ配信中ではない場合
            _, live_title, _, live_chat_id = self.get_upcoming_video(video_id)
            return live_title, live_chat_id
        else:
            # ライブ配信中の場合
            live_streaming_details, snippet = self.__get_live_videos(video_id)
            return snippet["title"], live_streaming_details["activeLiveChatId"]
        return None

    def get_live_chat_messages(self, live_chat_id, pageToken=None):
        if pageToken == None:
            live_chat_messages_result = self.api.liveChatMessages().list(
                    part="snippet", hl="ja", maxResults="2000",
                    liveChatId=live_chat_id
                ).execute()
        else:
            live_chat_messages_result = self.api.liveChatMessages().list(
                    part="snippet", hl="ja", maxResults="2000",
                    liveChatId=live_chat_id, pageToken=pageToken
                ).execute()
        return live_chat_messages_result["items"], live_chat_messages_result["pollingIntervalMillis"], live_chat_messages_result["nextPageToken"]
