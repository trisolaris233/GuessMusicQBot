import tools.track as track
import sqlite3
import json
import re
import random
import os
import shutil
from tools.coolq import *
import tools.netease as netease

class User:
    def __init__(self, user_id, group_id, permission, game_played=0, wins=0, id=0):
        self.user_id = user_id
        self.group_id = group_id
        self.permission = permission
        self.game_played = game_played
        self.wins = wins
        self.id = id

    def tostring(self):
        winrate = 0
        if self.wins != 0:
            winrate = round(self.wins/self.game_played * 100,0)
        msg = "id:{}\nuser_id: {}\npermission: {}\nmatch: {}\nwin: {}\nwin rate: {}%".format(
                self.id,
                self.user_id,
                self.permission,
                self.game_played,
                self.wins,
                winrate
            )
        return msg



##########################小工具
def is_number(s):
    try:
        int(s)
    except:
        return False
    return True

def if_arg_avail(args, index):
    try:
        args[index]
        return True
    except:
        return False

def get_arg_or(args, index, rev):
    if if_arg_avail(args, index):
        return args[index]
    return rev

def get_args_number(args):
    try:
        length = len(args)
        return length
    except:
        return 0

def get_server_max_id():
    conn = sqlite3.connect(track.server_db_path)
    c = conn.cursor();

    c.execute("SELECT * FROM sqlite_sequence WHERE name=?;",("USERSINFO",))
    res = c.fetchall()
    if len(res) == 0:
        return 0
    print(res)
    return res[0][-1]

def get_user_info(user_id, group_id)->User:
    conn = sqlite3.connect(track.server_db_path)
    cursor = conn.cursor()

    c = cursor.execute("SELECT * FROM USERSINFO WHERE USER_ID=? AND GROUP_ID=?;",(user_id, group_id))
    res = c.fetchall()
    if len(res) == 0:
        return None
    return User(res[0][1], res[0][2], res[0][3], res[0][4], res[0][5], res[0][0])

def parse_cq_code(s):
    prog = re.compile("\\[CQ:(.+?),(.+)?=(.+)\\]")
    try:
        groups = prog.search(s).groups()
        return groups
    except:
        return None

def parse_lyrics(lyric):
    if lyric == "no lyrics":
        return None

    statements = [x.strip() for x in lyric.split('\n') if x.strip()!='']
    prog = re.compile("\\[([0-9]+?)\\:([0-9]+?)\\.?([0-9]+?)\\](.*)")
    res = netease.Lyrics()

    for statement in statements:
        r = prog.search(statement)
        if not r:
            continue
        groups = r.groups()

        minutes = int(groups[0])
        second = int(groups[1])
        msecond = int(groups[2])
        flag = ':' in groups[3] or '：' in groups[3] or ":" in groups[3]

        res.lrc.append((flag, groups[3], minutes*60*1000+second*1000+msecond))

    return res

#############################


def reg_user(user_id, group_id):
    conn = sqlite3.connect(track.server_db_path)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO USERSINFO(USER_ID, GROUP_ID, PERMISSION, GAME_PLAYED, WINS) VALUES(?,?,?,?,?)",
        (user_id, group_id, 0, 0, 0))

    conn.commit()
    conn.close()
    try:
        return get_server_max_id()
    except:
        return 0

def get_permission(user_id, group_id):
    conn = sqlite3.connect(track.server_db_path)
    cursor = conn.cursor()

    c = cursor.execute("SELECT * FROM USERSINFO WHERE USER_ID=? AND GROUP_ID=?;",
        (user_id, group_id))
    res = c.fetchall()

    if len(res) == 0:
        return -1

    return res[0][3]

def check_permission(user_id, group_id, target, can_equal=True):
    permission = get_permission(user_id, group_id)
    if can_equal:
        return permission >= target
    return permission > target

def _get_games_of_a_status(group_id, status):
    conn = sqlite3.connect(track.server_db_path)
    cursor = conn.cursor()

    c = cursor.execute("SELECT * FROM GAMEDATA WHERE GROUP_ID=? AND STATUS=?",(group_id, status))

    return c.fetchall()

def get_games_established(group_id):
    return _get_games_of_a_status(group_id, 0)

def get_games_finished(group_id):
    return _get_games_of_a_status(group_id, 1)

def get_games_num_established(group_id):
    return len(get_games_established(group_id))

def get_games_num_finished(group_id):
    return len(get_games_finished(group_id))

def get_key_lyrics(group_id):
    games = get_games_established(group_id)
    if not games:
        return None
    game = games[0]
    return game[8]

def establish_game(user_id, group_id, mode=0):
    conn = sqlite3.connect(track.server_db_path)
    cursor = conn.cursor()

    if get_games_num_established(group_id) > 0:
        return 0

    cursor.execute("INSERT INTO GAMEDATA(\
        STATUS, GROUP_ID, MODE, MEMBERS, START_TIME) \
        VALUES(?,?,?,?,?);",
        (0, group_id, mode, ','.join([str(user_id)]), track.get_strf_local_time()))

    conn.commit()
    conn.close()
    return 1

def get_cursor_range():
    conn = sqlite3.connect(track.server_db_path)
    cursor = conn.cursor()

    c = cursor.execute("SELECT * FROM GLOBAL;")
    res = []
    try:
        res = c.fetchone()[0]
    except:
        return res
    return [int(x) for x in res]

def pick_music_randomly(group_id):
    random_id = random.randint(1, track.get_current_max_id())
    song = track.search_song_with_id(random_id, random_id)
    track_id = song[0][5]
    basename = "{}.mp3".format(track_id)
    filename = os.path.join(track.music_path, basename)
    download_url = netease.get_download_url(track_id)
    if track.download_music(download_url, filename) == 0:
        send_group_msg(group_id, "Downalod ERROR: VIP-Only Resoures, game will close automatically")
        end_game(group_id)
        return

    sec = random.randint(10, 25)
    start_sec = random.randint(0, song[0][4] - sec*1000)
    end_sec = start_sec + sec * 1000
    target_filename = os.path.join(track.music_path,"{}_.mp3".format(track_id))
    track.clip_music(filename, start_sec, end_sec, target_filename)
    shutil.copyfile(target_filename, os.path.join(track.coolq_record_path, basename))

    os.remove(filename)
    send_group_voice_msg(group_id, basename, track.coolq_record_path)

    conn = sqlite3.connect(track.server_db_path)
    cursor = conn.cursor()

    cursor.execute("UPDATE GAMEDATA SET TRACK_ID=? WHERE GROUP_ID=? AND STATUS=0", (track_id, group_id))
    conn.commit()
    conn.close()

def pick_music_randomly_ex(group_id):
    random_id = random.randint(1, track.get_current_max_id())
    song = track.search_song_with_id(random_id, random_id)
    track_id = song[0][5]
    lyric = song[0][7]
    print(lyric)
    duration_time = song[0][4]
    while True:
        if lyric == "no lyrics":
            random_id = random.randint(1, track.get_current_max_id())
            song = track.search_song_with_id(random_id, random_id)
            track_id = song[0][5]
            lyric = song[0][7]
            continue
        else:
            break

    lyrics = parse_lyrics(song[0][7])
    if not lyrics:
        return
    num_lyrics = len(lyrics.lrc)
    basename = "{}.mp3".format(track_id)
    filename = os.path.join(track.music_path, basename)
    download_url = netease.get_download_url(track_id)
    if track.download_music(download_url, filename) == 0:
        send_group_msg(group_id, "Downalod ERROR: VIP-Only Resoures, game will close automatically")
        end_game(group_id)
        return

    # 随机抽3句连续的歌词
    # 先找到第一句
    index = 0
    for lyric in lyrics.lrc:
        if lyric[0]:
            index+=1
        else:
            break

    # 随机抽一句
    rand_index = random.randint(index,num_lyrics-3)
    # 往后抽2句 [rand_index,rand_index_end]为3句
    rand_index_end = rand_index + 2
    
    start_sec = lyrics.lrc[rand_index][2]

    # 设置终止时间
    end_sec = 0
    if rand_index_end == num_lyrics - 1:
        end_sec = duration_time - 400 # 怕不准 减400ms保命
    else:
        end_sec = lyrics.lrc[rand_index_end + 1][2]

    target_filename = os.path.join(track.music_path,"{}_.mp3".format(track_id))
    # 剪切
    print("start_sec={} and end_sec={}".format(start_sec, end_sec))
    track.clip_music(filename, start_sec, end_sec, target_filename)
    shutil.copyfile(target_filename, os.path.join(track.coolq_record_path, basename))
    # 辣鸡文件去死
    os.remove(filename)

    # 放出来
    send_group_voice_msg(group_id, basename, track.coolq_record_path)
    
    # 把歌词插入数据库
    conn = sqlite3.connect(track.server_db_path)
    cursor = conn.cursor()

    c = cursor.execute("UPDATE GAMEDATA SET TRACK_ID=?, LYRICS_RESERVE=? WHERE STATUS=0 AND GROUP_ID=? AND MODE=1;",
        (track_id, lyrics.lrc[rand_index_end + 1][1], group_id))
    send_group_msg(group_id, "你的下一句话是:___")

    conn.commit()
    conn.close()
    
def start_game(group_id, mode=0):
    cursor_range = get_cursor_range()
    if mode == 0:
        if len(cursor_range) == 0:  
            pick_music_randomly(group_id)
        else:
            pass
    
    # 猜歌词模式
    elif mode == 1:
        send_group_msg(group_id, "now in lyrics-guess mode")
        pick_music_randomly_ex(group_id)
        pass

def join_in_game(user_id, group_id):
    players = get_game_current_member_list(group_id)
    players.append(user_id)
    gamedata = get_user_info(user_id, group_id)
    if not gamedata:
        reg_user(user_id, group_id)
    str_players = [str(player) for player in players]

    conn = sqlite3.connect(track.server_db_path)
    cursor = conn.cursor()

    cursor.execute("UPDATE GAMEDATA SET MEMBERS=? WHERE GROUP_ID=? AND STATUS=0",
        (','.join(str_players), group_id))

    conn.commit()
    conn.close()

def get_game_current_member_list(group_id):
    players = get_games_established(group_id)
    if len(players) == 0:
        return None
    return [int(player) for player in players[0][5].split(',')]

def update_player_info(user_id, group_id):
    members = get_game_current_member_list(group_id)
    if not members:
        return
    conn = sqlite3.connect(track.server_db_path)
    cursor = conn.cursor()
    for member in members:
        gamedata = get_user_info(member, group_id)
        game_played = gamedata.game_played
        wins = gamedata.wins

        if user_id == member:
            wins += 1
        cursor.execute("UPDATE USERSINFO SET GAME_PLAYED=?,WINS=? WHERE GROUP_ID=? AND USER_ID=?",
            (game_played + 1,  wins, group_id, member))

    conn.commit()
    conn.close()

def end_game(group_id, arg=-1,):
    conn = sqlite3.connect(track.server_db_path)
    cursor = conn.cursor()

    if arg < 0:
        game = get_games_established(group_id)
        if game:
            update_player_info(-1, group_id)
    else:
        update_player_info(arg, group_id)

    

    game = get_games_established(group_id)
    if not game:
        cursor.execute("UPDATE GAMEDATA SET STATUS=1 WHERE STATUS=0 AND GROUP_ID=?",(group_id,))
        conn.commit()
        conn.close()
        return


    track_id = game[0][4]
    lyrics_reserve = game[0][8]
    mode = game[0][3]

    if mode == 0:
        track_info = track.search_song_with_track_id(track_id)[0]
        name = track_info[1]
        artist = track_info[2]
        send_group_msg(group_id, "Game closed, this song is from {} - {}".format(name, artist))

    elif mode == 1:
        send_group_msg(group_id, "Game closed, the next sentence is \"{}\"".format(get_key_lyrics(group_id)))
    # game = get_games_established(group_id)
    # if game:
    #     track_id = game[0][4]
    #     if not track_id:
    #         update_player_info(-1, group_id)
    #         cursor.execute("UPDATE GAMEDATA SET STATUS=1 WHERE STATUS=0 AND GROUP_ID=?",(group_id,))
    #         return
    #     else:
    #         track_info = track.search_song_with_track_id(track_id)[0]
    #         send_group_msg(group_id, "Game ended, key is {} - {}".format(track_info[1], track_info[2]))

    # update_player_info(-1, group_id)
    cursor.execute("UPDATE GAMEDATA SET STATUS=1 WHERE STATUS=0 AND GROUP_ID=?",(group_id,))
    conn.commit()
    conn.close()

def change_permission(user_id, group_id, permission):
    conn = sqlite3.connect(track.server_db_path)
    cursor = conn.cursor()

    cursor.execute("UPDATE USERSINFO SET PERMISSION=? WHERE USER_ID=? AND GROUP_ID=?",(permission, user_id, group_id))

    conn.commit()
    conn.close()


def edit_track_name(tid, name):
    conn =sqlite3.connect(track.track_db_path)
    cursor = conn.cursor()

    cursor.execute("UPDATE TRACKS SET NAME=? WHERE ID=?",(name, tid))
    conn.commit()
    conn.close()
