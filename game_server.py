
from flask import Flask, redirect, url_for, escape, request, jsonify, make_response,session
import requests
import json
import time
import os
from datetime import timedelta
import sqlite3
import config
import re
from langconv import Converter #



def init_database():
    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''CREATE TABLE GAMEINFO(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            WINERQQ INT NOT NULL,
            MEMBER_JOINED INT NOT NULL
        );''')
    except:
        pass
    try:
        cursor.execute('''CREATE TABLE USERSINFO(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,            
            QQ INT NOT NULL,                    
            PERMISSION INT NOT NULL,
            GROUPID INT NOT NULL,
            GAME_PLAYED INT NOT NULL,
            WINS INT NOT NULL
            );''')
    except:
        pass
    
    conn.commit()
    conn.close()


app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
init_database()








def send_qqgroup_msg(groupid, msg):
    playload = {
      'group_id':"{}".format(groupid),
      'message':msg,
      'auto_escape':'false'
    }
    requests.get("http://localhost:5700/send_group_msg",params=playload)


def is_group_msg(json_data):
    return json_data['post_type'] == 'message' and json_data['message_type'] == 'group'

def is_private_msg(json_data):
    return json_data['post_type'] == 'message' and json_data['message_type'] == 'private'

def get_group_id(json_data):
    return json_data['group_id']

def get_private_id(json_data):
    return json_data['user_id']

def write_user_info(qq, group_id):
    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()
    c = cursor.execute("INSERT INTO USERSINFO(QQ,PERMISSION,GROUPID,GAME_PLAYED,WINS) VALUES(?,?,?,?,?)",(
        qq,
        0,
        group_id,
        0,
        0
    ))
    conn.commit()
    conn.close()

def join_in_game(qq,group_id):
    pass



def set_permission(target_user_id, target_level, json_data):
    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()

    cursor.execute("UPDATE USERSINFO SET PERMISSION = ? WHERE QQ =? AND GROUPID=?;",
        (target_level, target_user_id,get_group_id(json_data)))
    conn.commit()
    conn.close()

def get_permission(qq, groupid):
    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()
    c = cursor.execute("SELECT * FROM USERSINFO WHERE QQ={} AND GROUPID={}".format(
        qq, groupid
    ))
    res = c.fetchall()
    if len(res) <= 0:
        write_user_info(qq, groupid)
        return 0

    return res[0][2]

def treat_group_msg(json_data):
    msg = json_data['message']
    qq = json_data['user_id']
    group_id = get_group_id(json_data)

    if msg == "?permission":
        permission = get_permission(qq, group_id)
        send_qqgroup_msg(group_id, "[CQ:at,qq={}],your permission is {}".format(
            qq, permission
            ))

    elif msg == "?games":
        send_qqgroup_msg(get_group_id(json_data),'''
            LIST OF GAMES AVAIL\n
            - RecogTune Given a piece of music and guess the name of the song.
            ''')

    elif msg == "?ddf":
        send_qqgroup_msg(get_group_id(json_data),"Deep♂Dark♂Fantasy")

    elif msg.startswith("?gtper"):
        ls = msg.split(' ')
        if len(ls) < 2:
            return
        try:
            target_user_id = eval(ls[1])
        except:
            return

        send_qqgroup_msg(
            get_group_id(json_data),
            "[CQ:at,qq={}], {}'s permission is {}".format(
                qq,target_user_id,get_permission(target_user_id,get_group_id(json_data))))


    elif msg.startswith("?chper"):
        ls = msg.split(' ')
        if len(ls) < 3:
            return
        try:
            target_user_id = eval(ls[1])
            target_level = eval(ls[2])
        except:
            return
        

        permission = get_permission(qq,group_id)
        target_permission = get_permission(target_user_id, group_id)
        if (permission <= 4):
            at_and_say(group_id,qq,"permission denied to set permission")
        else:
            if permission < 6:
                if target_level > 3:
                    at_and_say(group_id,qq,"Unable to set permission to {} for your are not allowed to do so in your permission.".format(target_level))
                else:
                    set_permission(target_user_id, target_level, json_data)
                    at_and_say(group_id,qq,"Successful operation")

            else:
                if target_level > 5:
                    at_and_say(group_id,qq," Unable to set permission to {} for your are not allowed to do so in your permission.".format(target_level))
                    
                else:
                    set_permission(target_user_id, target_level, json_data)
                    at_and_say(group_id,qq,"Successful operation")


    elif msg == "?prestart":
        permission = get_permission(qq, group_id)
        if permission < 6:
            at_and_say(group_id,qq,"permission denied for you to establish a game.")
        else:
            # 准备游戏 获得gameid
            game_id = prestart_game(json_data)
            if game_id == -1:
                at_and_say(group_id,qq,"There's game unfinished, admin enter ?endg to end this game.")
                return

            send_qqgroup_msg(group_id, "A new game established! game_id = {}. enter ?join to join in this game.".format(game_id))


    elif msg == "?join":
        permission = get_permission(qq, group_id)
        if permission >= 0:
            if join_in_game(qq, group_id):
                at_and_say(group_id, qq, "You've joined the game successfuly!")
        else:
            at_and_say(group_id, qq, "You're banned to join any game!")


    elif msg == "?start":
        if check_permission(qq,group_id,5):
            start_current_game(group_id)
            return
        else:
            at_and_say(group_id,qq,"permission denied to start game!")
    elif msg == "?end":
        if check_permission(qq,group_id,5):
            end_current_game(group_id)
            at_and_say(group_id, qq, "all the games are expired now")
        else:
            at_and_say(group_id, qq, "permission denied to end current game")


    elif msg.startswith("?info"):
        ls = msg.split(' ')
        if len(ls) < 1:
            return
        if len(ls) == 1:

            info = get_user_info(group_id, qq)
            game_played = info[4]
            wins = info[5]
            msg = "\ngame played: {}\nwin: {}\nwin rate: {}%".format(game_played,wins,wins/game_played*100)
            at_and_say(group_id, qq, msg)

        else:
            info = get_user_info(group_id, ls[1])
            game_played = info[4]
            wins = info[5]
            msg = "\nplayer:{}\ngame played: {}\nwin: {}\nwin rate: {}%".format(ls[1], game_played,wins,wins/game_played*100)
            at_and_say(group_id, qq, msg)



    # 检查游戏进行状态
    # 如果有游戏在进行
    # 则要对消息进行监控
    if game_is_running(group_id) and is_joined(group_id, qq):
        if not msg.startswith("guess "):
            return

        res = match_key_and_msg(group_id, qq, msg[6:])
        if res == 1:
            at_and_say(group_id, qq, "Perfect match! You win!")
            set_winner(group_id, qq)
            end_current_game(group_id)
            send_qqgroup_msg(group_id, "winner is [CQ:at,qq={}], the game is closed automatically.".format(qq))

        elif res == 2:
            at_and_say(group_id, qq, "You matched part of its name")
        elif res == -1:
            at_and_say(group_id, qq, "Single letter is not supported to do match")
        elif res == -2:
            at_and_say(group_id, qq, "invalid letter")
        elif res == -3:
            at_and_say(group_id, qq, "unknown error")
        elif res == 0:
            at_and_say(group_id, qq, "You got wrong, try again.")
            #at_and_say()
    else:
        pass


# 设置胜者
def set_winner(group_id, qq):
    pass


def at_and_say(group_id, qq, msg):
    send_qqgroup_msg(group_id, "{}{}".format("[CQ:at,qq={}] ".format(qq),msg))


def check_permission(qq,group_id,target):
    return get_permission(qq, group_id) > target

def treat_private_msg(json_data):
    pass


def is_joined(group_id, qq):
    return qq in get_current_game_data_members(group_id,1)

# 获取未结束的游戏
# GAME_STAUTS可能值:0 准备中 1 正在进行 2 已结束
def get_games_running(group_id):
    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()

    c = cursor.execute("SELECT * FROM GAMEDATA WHERE GAME_STATUS=? AND GROUPID=?;",(1,group_id))
    res = c.fetchall()

    return len(res)

# 获取未结束的游戏
# GAME_STAUTS可能值:0 准备中 1 正在进行 2 已结束
def get_games_unfinished(group_id):
    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()

    c = cursor.execute("SELECT * FROM GAMEDATA WHERE GAME_STATUS=? AND GROUPID=?;",(0,group_id))
    res = c.fetchall()

    return len(res)


def game_is_running(group_id):
    num = get_games_running(group_id)
    return num > 0


def start_current_game(group_id):
    num = get_games_unfinished(group_id)

    if num == 1:
        conn = sqlite3.connect("server.db")
        cursor = conn.cursor()

        c = cursor.execute("UPDATE GAMEDATA SET GAME_STATUS=? WHERE GROUPID=? AND GAME_STATUS=?",(1,group_id,0))

        conn.commit()
        conn.close()

        print("python music_picker.py {}".format(group_id))
        os.system("python music_picker.py {}".format(group_id))

def get_user_info(group_id, qq):
    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()

    c = cursor.execute("SELECT * FROM USERSINFO WHERE GROUPID=? AND QQ=?;",(group_id,qq))

    return c.fetchall()[0]


def get_current_game_data(group_id, game_status):
    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()

    c = cursor.execute("SELECT * FROM GAMEDATA WHERE GROUPID=? AND GAME_STATUS=?",(group_id,game_status))
    try:
        return c.fetchall()[0]
    except:
        return None

def get_current_game_data_members(group_id, game_status):
    try:
        return eval(get_current_game_data(group_id, game_status)[7])
    except:
        return None

def increase_game_info(group_id, qq):
    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()

    info = get_user_info(group_id, qq)
    game_played = info[4] + 1

    print(game_played)

    cursor.execute("UPDATE USERSINFO SET GAME_PLAYED=? WHERE GROUPID=? AND QQ=?;",(game_played, group_id, qq))
    conn.commit()
    conn.close()


def set_winner(group_id, winner):
    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()

    info = get_user_info(group_id, winner)
    wins = info[5] + 1

    cursor.execute("UPDATE USERSINFO SET WINS=? WHERE QQ=?;",(wins,winner))
    conn.commit()
    conn.close()

def end_current_game(group_id):
    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()

    members = get_current_game_data_members(group_id, 1)
    if members:
        for member in members:
            increase_game_info(group_id, member)


    cursor.execute("UPDATE GAMEDATA SET GAME_STATUS=? WHERE (GAME_STATUS=? OR GAME_STATUS=?) AND GROUPID=?;",(2,0,1,group_id))
    conn.commit()
    conn.close()


def get_key_info(group_id):
    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()

    c = cursor.execute("SELECT * FROM GAMEDATA WHERE GROUPID=? AND GAME_STATUS=?;",(group_id,1))
    return c.fetchall()[0]



def join_in_game(qq, group_id):
    num = get_games_unfinished(group_id)

    if num == 0:
        at_and_say(group_id, qq, "There's no game to join")
        return 0

    if num > 1:
        at_and_say(group_id, qq, "There're too many games established, end them and continue")
        return 0

    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()

    c = cursor.execute("SELECT * FROM GAMEDATA WHERE GROUPID=? AND GAME_STATUS=?",(group_id, 0))
    res = c.fetchall()
    if len(res) < 1:
        return 0

    members = eval(res[0][7])
    if qq in members:
        at_and_say(group_id,qq,"You've already joined in this game!")
        return 0
    else:
        members.append(qq)
        cursor.execute("UPDATE GAMEDATA SET MEMBER=? WHERE GROUPID=? AND GAME_STATUS=?",(json.dumps(members),group_id,0))

    conn.commit()
    conn.close()
    return 1


def is_cq_code(msg):
    return msg.startswith("[CQ:")


def match_key_and_msg(group_id, qq, msg):
    print(msg)
    msg = str.lower(msg)
    if msg == "":
        return 0

    if msg.startswith("?"):
        return 0

    if is_cq_code(msg):
        return 0

    key_info = get_key_info(group_id)
    name = str.lower(key_info[1])
    
    # 单个字符搜索
    if len(msg) == 1:
        # 如果是中文就可以强化搜索
        # 如果是英文 数字 符号就不能算
        # 暂时只支持日语的汉字
        if is_chinese_letter(msg[0]):
            _msg = chs_to_cht(msg)[0]
            res = re.search(_msg, name)
            res2 = re.search(msg, name)
            # 如果找到了 就返回一个值
            if res or res2:
                return 2
            else:
                return 0

        # 不支持单个英文字符的搜索
        elif str.isalpha(msg):
            return -1

        # 查是否有特殊字符
        res = re.search(r"\W",msg)
        if res:
            return -2
        return -3


    # 多个字符搜索
    if msg == name:
        return 1

    res = re.search(msg, name)
    _msg = ''.join(chs_to_cht(msg))
    print(_msg)
    res2 = re.search(msg, name)

    if res or res2 :
        return 2

    return 0








# 游戏管理员预开始游戏
# 等待?join来加入游戏或者?exit来退出游戏
# 先检查有没有未结束的游戏
# 然后开始新游戏
def prestart_game(json_data):
    group_id = get_group_id(json_data)
    num_game_unfinished = get_games_unfinished(group_id)

    if num_game_unfinished != 0:
        
        return -1;

    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO GAMEDATA(GAME_STATUS, MEMBER, GROUPID) VALUES(?,?,?);",(0,json.dumps([]), group_id))
    conn.commit()
    conn.close()

    lastrowid = cursor.lastrowid

    
    return cursor.lastrowid




'''
CREATE TABLE GAMEDATA(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    NAME TEXT,
    TRACKID INT,
    START_TIME INT,
    END_TIME INT,
    GAME_STATUS INT,
    MANAGER INT,
    MEMBER TEXT,
    GROUPID INT,
    GAME_START_TIME TIME,
    GAME_END_TIME TIME,
    WINNER INT
    );
'''



# 音乐下载程序请求
# 得到必要的游戏数据
@app.route('/set_game_data',methods=['POST'])
def set_game_data():
    data = request.get_data()
    json_data = json.loads(data.decode("utf-8"))


    name = json_data['name']
    track_id = json_data['track_id']
    start_time = json_data['start_time']
    end_time = json_data['end_time']
    group_id = json_data['group_id']

    conn = sqlite3.connect("server.db")
    cursor = conn.cursor()

    cursor.execute('''UPDATE GAMEDATA SET NAME=?,TRACKID=?,START_TIME=?,END_TIME=? WHERE GROUPID=? AND GAME_STATUS=?;
        ''', (name, track_id, start_time, end_time, group_id, 1))


    conn.commit()
    conn.close()

    return "200 OK"




@app.route('/watch', methods=['POST'])
def watch_msg():
    data = request.get_data()
    json_data = json.loads(data.decode("utf-8"))

    if (is_group_msg(json_data)):
        treat_group_msg(json_data)

    if (is_private_msg(json_data)):
        treat_private_msg(json_data)

    return jsonify(block="false")



def cat_to_chs(sentence): #传入参数为列表
    """
    将繁体转换成简体
    :param line:
    :return:
    """
    sentence =",".join(sentence)
    sentence = Converter('zh-hans').convert(sentence)
    sentence.encode('utf-8')
    return sentence.split(",")


def chs_to_cht(sentence):#传入参数为列表
    """
    将简体转换成繁体
    :param sentence:
    :return:
    """
    sentence =",".join(sentence)
    sentence = Converter('zh-hant').convert(sentence)
    sentence.encode('utf-8')
    return sentence.split(",")

#检验是否全是中文字符
def is_all_chinese(strs):
    for _char in strs:
        if not '\u4e00' <= _char <= '\u9fa5':
            return False
    return True

def is_chinese_letter(str):
    return '\u4e00' <= str <= '\u9fa5'


