from urllib.parse import urlparse,parse_qs  
import requests
from pydub import AudioSegment
import json
import os


music_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "music")

class Track:
    def __init__(self, track_id, name, artist_name, album_name, duration_time, download_url):
        self.track_id = track_id
        self.name = name
        self.artist_name = artist_name
        self.album_name = album_name
        self.duration_time = duration_time
        self.download_url = download_url

# 传入歌单url或者歌曲url 返回对应的id
def parse_netease_share_url(url):
    res = urlparse(url)
    query = res.query
    path = res.path
    if not query or not path:
        return (0,)

    query_dict = parse_qs(query)

    real_path = str.lower(path[1:])
    print(real_path )
    if (real_path == "playlist"):
        return (1, query_dict['id'][0])
    elif (real_path == "song"):
        return (2, query_dict['id'][0])

    return (0,)

def get_detail(id):
    try:
        print(id)
        res = requests.get("https://v1.hitokoto.cn/nm/detail/{}".format(id))
        res_data = json.loads(res.text)
        print(res_data)
        data = res_data['songs'][0]
        name = data['name']
        track_id = data['id']
        album_name = data['al']['name']
        duration_time = data['dt']
        artist_name = [artist['name'] for artist in data['ar']]
        download_url = get_download_url(id)

        return Track(track_id,name,json.dumps(artist_name),album_name,duration_time,download_url)
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


