import requests
import sqlite3
import os
import sys
import time
from pydub import AudioSegment
import tools.netease as netease

server_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"data","server.db")
track_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"data","tracks.db")

def init():
    global track_db_path
    print(track_db_path)
    conn = sqlite3.connect(track_db_path)
    c = conn.cursor();
    try:
        c.execute('''CREATE TABLE TRACKS(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NAME TEXT NOT NULL,
            ARTIST_NAME TEXT NOT NULL,
            ALBUM_NAME TEXT NOT NULL,
            DURATION_TIME INT NOT NULL,
            TRACK_ID INT NOT NULL,
            DOWNLOAD_URL TEXT NOT NULL
        );''')
    except Exception as e:
        print(e)
        pass
    try:
        # 歌曲库操作表
        # OPERATION 代表操作 有增删改查4种操作
        # 分别代表0 1 2 3

        # FROMID 代表如果是增或者改的时候 歌曲或者歌单的来源
        # ID_START 代表被改的ID 比如添加歌曲 当前最大ID是99 就要从100开始
        # OPERATION_RANGE 代表操作范围
        # EXPLAIN 可以在增的时候添加
        # USER_ID 操作者的QQ
        # GROUP_ID 操作所在的群
        # OPERATION_TIME 操作的时间
        c.execute('''CREATE TABLE OPERATIONS_RECORD(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            OPERATION INT NOT NULL, 
            FROM_ID INT,
            ID_START INT NOT NULL,
            OPERATION_RANGE INT NOT NULL,
            EXPLAIN TEXT,
            USER_ID INT,
            GROUP_ID INT,
            OPERATION_TIME DATE
        );''')
    except Exception as e:
        print(e)
        pass

    conn.commit()
    conn.close()


def download_music(download_url, filename):
    try:
        music = requests.get(download_url)
        with open(filename, "wb") as f:
            f.write(music.content)
            f.close()
        return 1
    except:
        return 0

def clip_music(path, start, end, filename):
    music = AudioSegment.from_mp3(path)
    if end == -1:  
        music[start:].export(filename, format="mp3")
    else:
        music[start:end].export(filename, format="mp3")
    pass

def get_track_count():
    conn = sqlite3.connect(track_db_path)
    c = conn.cursor();

    c.execute("SELECT COUNT(*) FROM TRACKS;")
    return c.fetchone()[0]

def get_current_max_id():
    conn = sqlite3.connect(track_db_path)
    c = conn.cursor();

    c.execute("SELECT * FROM sqlite_sequence WHERE name=?;",("TRACKS",))
    res = c.fetchall()
    if len(res) == 0:
        return 0
    print(res)
    return res[0][-1]

def get_strf_local_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 

def update_operation(operation, id_start, operation_range, user_id=0, group_id=0, explain='', from_id=''):
    conn = sqlite3.connect(track_db_path)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO OPERATIONS_RECORD(OPERATION, ID_START,OPERATION_RANGE, USER_ID, GROUP_ID, EXPLAIN, FROM_ID, OPERATION_TIME)"
        "VALUES(?,?,?,?,?,?,?,?);", 
        (operation, id_start, operation_range, user_id, group_id, explain, from_id, get_strf_local_time()))
    conn.commit()
    conn.close()



def import_playlist(id, user_id=0, group_id=0, explain=''):
    conn = sqlite3.connect(track_db_path)
    c = conn.cursor();
    json_data = requests.get("https://v1.hitokoto.cn/nm/playlist/{}".format(id)).json()
    tracks = json_data['playlist']['tracks']
    max_id = get_current_max_id()
    operation_range = len(tracks)
    for track in tracks:

        name = track['name']
        artist_name = track['ar'][0]['name']
        album_name = track['al']['name']
        duration_time = track['dt']
        track_id = track['id']
        download_url=netease.get_download_url(track_id)
        c.execute('''INSERT INTO TRACKS(
        NAME,ARTIST_NAME,ALBUM_NAME,DURATION_TIME,TRACK_ID,DOWNLOAD_URL)

        VALUES(?,?,?,?,?,?)''',(name,artist_name,album_name,duration_time,track_id,download_url ))
    conn.commit()
    update_operation(0, max_id + 1, operation_range, user_id, group_id, explain, id)


    conn.commit()
    conn.close()

    return (max_id + 1, len(tracks))


def remove_track_with_id(start_id, end_id=-1, user_id=0, group_id=0):
    res = search_song_with_id(start_id, end_id, user_id, group_id)
    conn = sqlite3.connect(track_db_path)
    cursor = conn.cursor()
    

    operation_range = 1
    str_sql = "DELETE FROM TRACKS WHERE ID >=?"
    if end_id != -1 and end_id >= start_id:
        str_sql += " AND ID <= ?;"
        print(str_sql)
        cursor.execute(str_sql, (start_id, end_id))
        operation_range = end_id - start_id + 1
    else:
        cursor.execute(str_sql+";", (start_id, ))

    conn.commit()
    conn.close()

    update_operation(1, start_id, operation_range, user_id, group_id)
    return res

def search_song_with_name(name, end_id=-1, user_id=0, group_id=0):
    conn = sqlite3.connect(track_db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM TRACKS WHERE NAME LIKE ?;",('%' + name + '%',))
    return cursor.fetchall()

def search_song_with_artist_name(artist_name, end_id=-1, user_id=0, group_id=0):
    conn = sqlite3.connect(track_db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM TRACKS WHERE ARTIST_NAME LIKE ?;",('%' + artist_name + '%',))
    return cursor.fetchall()

def search_song_with_album_name(album_name, end_id=-1, user_id=0, group_id=0):
    conn = sqlite3.connect(track_db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM TRACKS WHERE ALBUM_NAME LIKE ?;",('%' + album_name + '%',))
    return cursor.fetchall()


def search_song_with_track_id(track_id):
    conn = sqlite3.connect(track_db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM TRACKS WHERE TRACK_ID=?",(track_id,))
    return cursor.fetchall()


def search_song_with_id(start_id, end_id=-1, user_id=0, group_id=0):
    conn = sqlite3.connect(track_db_path)
    cursor = conn.cursor()

    str_sql = "SELECT * FROM TRACKS WHERE ID >= ?"
    if end_id != -1 and end_id >= start_id:
        str_sql += "AND ID <= ?;"
        cursor.execute(str_sql, (start_id, end_id))
    else:
        cursor.execute(str_sql+";",(start_id,))

    res = cursor.fetchall()
    conn.close()
    return res

def output_track_list(list_of_tracks):
    if not list_of_tracks:
        return "no TRACKS"
    length = len(list_of_tracks)
    msg = ""
    if length > 8:
        msg = "The list includes {} tracks.".format(length)
    else:
        for track in list_of_tracks:
            msg += '{} -'.format(track[0]) + track[1] + ' - {}\n'.format(track[2])
    return msg


def import_song(id, user_id =0, group_id=0, explain=''):
    obj = netease.get_detail(id)
    if not obj:
        return 0

    conn = sqlite3.connect(track_db_path)
    c = conn.cursor();
    max_id = get_current_max_id ()

    c.execute('''INSERT INTO TRACKS(
        NAME, ARTIST_NAME,ALBUM_NAME,DURATION_TIME,TRACK_ID,DOWNLOAD_URL
        ) VALUES(?,?,?,?,?,?);''',
        (obj.name, obj.artist_name, obj.album_name, obj.duration_time, obj.track_id, obj.download_url))
    conn.commit()
    update_operation(0, max_id + 1, 1, user_id, group_id, explain, id)

    conn.commit()
    conn.close()

    return (max_id + 1,1)


def import_from_url(url, user_id=0,group_id=0, explain='' ):
    rev = netease.parse_netease_share_url(url)
    status_value = rev[0]

    # 导入歌单
    if status_value == 1:
        return import_playlist(rev[1], user_id, group_id, explain)
    elif status_value == 2:
        return import_song(rev[1], user_id, group_id, explain)
    return None