import sqlite3
import requests
import json
import argparse

parser = argparse.ArgumentParser()

def init():
    conn = sqlite3.connect("tacks.db")
    c = conn.cursor();

    c.execute('''CREATE TABLE TRACKS(
        ID INT PRIMARY KEY NOT NULL,
        NAME TEXT NOT NULL,
        ARTIST_NAME TEXT NOT NULL,
        ALBUM_NAME TEXT NOT NULL,
        DURATION_TIME INT NOT NULL,
        TRACK_ID INT NOT NULL
    );''')

    conn.commit()
    conn.close()

def init_parser():
    parser.add_argument("playlist_id")


def get_count():
    conn = sqlite3.connect("tracks.db")
    c = conn.cursor();

    c.execute("SELECT COUNT(*) FROM TRACKS;")
    return c.fetchall()[0][0]


def main():
    init_parser()
    args = parser.parse_args()
    try:
        init()
    except:
        pass
    conn = sqlite3.connect("tracks.db")
    c = conn.cursor();
    json_data = requests.get("https://v1.hitokoto.cn/nm/playlist/{}".format(args.playlist_id)).json()
    tracks = json_data['playlist']['tracks']
    i = get_count() + 1
    for track in tracks:
        name = track['name']
        artist_name = track['ar'][0]['name']
        album_name = track['al']['name']
        duration_time = track['dt']
        track_id = track['id']

        c.execute('''INSERT INTO TRACKS(ID,
        NAME,ARTIST_NAME,ALBUM_NAME,DURATION_TIME,TRACK_ID)

        VALUES(?,?,?,?,?,?)''',(i,name,artist_name,album_name,duration_time,track_id))
        i = i + 1
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()