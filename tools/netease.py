from urllib.parse import urlparse,parse_qs  
import requests
from pydub import AudioSegment
import json
import os
import re


music_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "music")

class Track:
    def __init__(self, track_id, name, artist_name, album_name, duration_time, status, lyrics):
        self.track_id = track_id
        self.name = name
        self.artist_name = artist_name
        self.album_name = album_name
        self.duration_time = duration_time
        self.status = status
        self.lyrics = lyrics

class Lyrics:
    def __init__(self):
        self.lrc = []


# 传入歌单url或者歌曲url 返回对应的id
def parse_netease_share_url(url):
    prog = re.compile("https?://music.163.com(/#)?/(song|playlist)(\\?id=|/)([0-9]+)")
    groups = prog.search(url).groups()
    print("groups = ",groups)
    if not groups:
        return (0, )
    
    real_path = groups[1].lower()
    if (real_path == "playlist"):
        return (1, int(groups[-1]))
    elif (real_path == "song"):
        return (2, int(groups[-1]))

    return (0,)

def get_lyrics(id):
    try:
        res = requests.get("https://v1.hitokoto.cn/nm/lyric/{}".format(id))
        res_data = json.loads(res.text)
        data = res_data['lrc']['lyric']

        return data
    except:
        return "no lyrics"
        pass

def get_detail(id):
    try:
        res = requests.get("https://v1.hitokoto.cn/nm/detail/{}".format(id))
        res_data = json.loads(res.text)
        data = res_data['songs'][0]
        name = data['name']
        track_id = data['id']
        album_name = data['al']['name']
        duration_time = data['dt']
        artist_name = ','.join([artist['name'] for artist in data['ar']])

        return Track(track_id,name,artist_name,album_name,duration_time, 1,get_lyrics(id))
    except Exception as e:
        print(e)
        return None

def get_download_url(id):
    try:
        res = requests.get("https://v1.hitokoto.cn/nm/url/{}".format(id))
        res_data = json.loads(res.text)
        music_url = res_data['data'][0]['url']
        if not music_url:
            return "failed"
        return music_url
    except:
        return "failed"

def get_name(id):
    pass

def get_artist_name(id):
    pass

def get_album_name(id):
    pass

def get_duration_time(id):
    pass


