import tools.track as track
import os
from flask import Flask, request, jsonify
import sqlite3
import json
import tools.config as config
import tools.plugins as plugins

def init_database():
    print(track.server_db_path)
    conn = sqlite3.connect(track.server_db_path)


    cursor = conn.cursor()

    try:
        cursor.execute('''CREATE TABLE USERSINFO(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            USER_ID INT NOT NULL,
            GROUP_ID INT NOT NULL,
            PERMISSION INT NOT NULL,
            GAME_PLAYED INT NOT NULL,
            WINS INT NOT NULL
            );''')
    except:
        pass

    # gamedata保存游戏进行时的内容
    # STATUS 为0的被视为进行时数据
    # STATUS 为1的被视为完成时数据
    # 每一个group只能有一个进行时的游戏
    # 但是进行时的游戏可以在不同的群保持独立
    # 用track_id来保存歌曲信息
    try:
        cursor.execute('''CREATE TABLE GAMEDATA(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            STATUS INT NOT NULL,
            GROUP_ID INT NOT NULL,
            MODE INT NOT NULL,
            TRACK_ID INT,
            MEMBERS TEXT,
            WINNER_ID INT,
            START_TIME DATE NOT NULL
            );''')
    except:
        pass

    conn.commit()
    conn.close()

def get_post_msg(request):
    data = request.get_data()
    json_data = json.loads(data.decode("utf-8"))
    return json_data

def is_group_msg(post_msg):
    return post_msg['post_type'] == 'message' and post_msg['message_type'] == 'group'



'''
此函数负责解析消息
返回(命令名,参数列表)
'''
def parse_msg(msg):
    stripped_msg = str.strip(msg)
    res = [x for x in stripped_msg.split(' ') if x]
    if len(res) < 2:
        return [res[0],None]
    return [res[0], res[1:]]

'''
核心方法 treat_group_msg
函数假定传入的一定是群消息 并能正常获得字段 这些要由调用方保证

'''
def treat_group_msg(post_msg):
    # 获得三个最主要字段
    msg = post_msg['message']

    res = parse_msg(msg)
    

    print("try")
    print(res)
    config.CALL_COMMAND[res[0]](res[1], post_msg)

















app = Flask(__name__)
init_database()



@app.route('/watch',methods=['POST'])
def watch():
    print(request)
    post_msg = get_post_msg(request)

    if is_group_msg(post_msg):
        treat_group_msg(post_msg)

    return jsonify(block="false")


