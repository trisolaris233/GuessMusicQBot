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

def start_game(group_id, mode=0):
    cursor_range = get_cursor_range()
    if len(cursor_range) == 0:  
        random_id = random.randint(1, track.get_current_max_id())
        song = track.search_song_with_id(random_id, random_id)
        track_id = song[0][5]
        basename = "{}.mp3".format(track_id)
        filename = os.path.join(track.music_path, basename)
        download_url = netease.get_download_url(track_id)
        track.download_music(download_url, filename)

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
    else:
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

def end_game(group_id):
    conn = sqlite3.connect(track.server_db_path)
    cursor = conn.cursor()

    game = get_games_established(group_id)
    if game:
        track_id = game[0][4]
        if not track_id:
            update_player_info(-1, group_id)
            cursor.execute("UPDATE GAMEDATA SET STATUS=1 WHERE STATUS=0 AND GROUP_ID=?",(group_id,))
            return
        else:
            track_info = track.search_song_with_track_id(track_id)[0]
            send_group_msg(group_id, "Game ended, key is {} - {}".format(track_info[1], track_info[2]))

    update_player_info(-1, group_id)
    cursor.execute("UPDATE GAMEDATA SET STATUS=1 WHERE STATUS=0 AND GROUP_ID=?",(group_id,))
    conn.commit()
    conn.close()



def change_permission(user_id, group_id, permission):
    conn = sqlite3.connect(track.server_db_path)
    cursor = conn.cursor()

    cursor.execute("UPDATE USERSINFO SET PERMISSION=? WHERE USER_ID=? AND GROUP_ID=?",(permission, user_id, group_id))

    conn.commit()
    conn.close()