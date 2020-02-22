
import requests
import json
import sys
from urllib.parse import urlparse
from urllib.parse import parse_qs
import re
from pydub import AudioSegment
import argparse
import random
import shutil
import sqlite3
import os
'''
usage:
main [-h] url [start_time] [end_time] --answer=choice [choices ...]


Choices are the candidates whatever you want refer to the title of a single song.

eg:
main https://music.163.com/song?id=3019798&userid=2040510536 60s 80s 'Lost Rivers' 'Zombies on Your Lawn' '粉红色的回忆' 'Viva la Vida'
'''


class BaseError(Exception):
    def __init__(self):
        self.err_msg = ""
        self.err_msg_detail = ""


class BadCommandError(BaseError):
    def __init__(self, msg):
        self.err_msg = msg
        self.err_msg_detail = msg
        Exception.__init__(self, msg, msg)

class BadUrlError(BaseError):
    def __init__(self, msg):
        self.err_msg = msg
        self.err_msg_detail = msg
        Exception.__init__(self, msg, msg)

parser = argparse.ArgumentParser()
def init_parser():
    parser.add_argument("link", help="网易云音乐的链接")
    parser.add_argument("start",help="开始时间")
    parser.add_argument("-e","--end",help="终止时间")
    parser.add_argument("answer",help="答案")
    parser.add_argument("-c","--choices",dest="choices",nargs='+')


def init_parser_random_ver():
    parser.add_argument("groupid", help="groupid")



def read_config(key):
    json_data = {}
    try:
        with open("config.json", "r") as f:
            json_data = json.loads(f.read())
    except:
        return None

    return json_data[key]

def read_config():
    json_data = {}
    try:
        with open("config.json", "r") as f:
            json_data = json.loads(f.read())
    except:
        dic = {
            'music_count':0
        }
        with open("config.json", "w+") as f:
            f.write(json.dumps(dic))
        return dic

    return json_data


def write_config(dic):
    with open("config.json", "w+") as f:
        f.write(json.dumps(dic))

def update_music_count():
    config = read_config()
    config['music_count'] = config['music_count'] + 1
    write_config(config)


'''
@description: 
@param {type} 
@return: tuple of url,start time and end time, and titles. no check. if errors occur, it will throw BadCommandError
'''
def parse_command(cmd):
    if len(cmd) < 2:
        raise BadCommandError("")

    return cmd[1:]


'''
@description: 
@param {type} 
@return: return string of id
'''

def parse_share_url(url):
    result = urlparse(url)
    if result.query == None:
        raise BadUrlError("")

    query_dict = parse_qs(result.query)
    music_id = query_dict['id']

    return music_id[0]



def calculate_time(arg):
    list_of_start_time = filter(lambda x:x!="",re.split("(min|m|sec|s)",arg))
    sec_start = 0
    tmp = 0
    min_start = 0
    for e in list_of_start_time:
        if e == "min" or e == "m":
            min_start = eval(tmp)*60*1000
        if e == "sec" or e =="s":
            sec_start = eval(tmp)*1000;
        tmp = e

    return min_start+sec_start;
'''
@description: 
@param {type} 
@return: align the unit to microsecond.
'''
def parse_time_and_duration(start, end):
    return calculate_time(end.tolower()) - calculate_time(end.lower())



'''
@description: 
@param {type} 
@return: None.
'''
def download_music(id, filename):
    res = requests.get("https://v1.hitokoto.cn/nm/url/{}".format(id))
    res_data = json.loads(res.text)
    music_url = res_data['data'][0]['url']
    print(music_url)
    music = requests.get(music_url)
    with open(filename, "wb") as f:
        f.write(music.content)
        f.close()
    update_music_count();

'''
@description: 
@param {type} 
@return: None.
'''
def clip_music(path, start, end, filename):
    music = AudioSegment.from_mp3(path)
    if end == -1:  
        music[start:].export(filename, format="mp3")
    else:
        music[start:end].export(filename, format="mp3")
    pass


'''
@description: 
@param {type} 
@return: None.
'''
def generate_html(music_url, answer, choices, filename):
    s = ""
    li_str = ""
    with open("template_html.html",mode="r",encoding="UTF-8") as f:
        s = f.read()
        li_str = "<div style=\"text-align:center;\">"
        i = 0
        case = random.randint(0, len(choices))
        for choice in choices:
            title = choice
            choice_html = ""
            if i == case:
                choice_html = "<label><input type=\"radio\" name=\"title\" value=\"{}\">{}</label></br>".format(i,answer)
                i = i + 1
            choice_html = choice_html + "<label><input type=\"radio\" name=\"title\" value=\"{}\">{}</label></br>".format(i,title)
            li_str = "{}{}".format(li_str,choice_html)
            i = i + 1

        li_str = "{}{}".format(li_str,"<button type=\"button\" onclick=\"judge()\">Submit</button>")

    js_code = '''
         function judge(){{
            var answer = {answer}
            var radios = document.getElementsByName("title");
            for(var i=0;i<radios.length;i++){{
                if(radios[i].checked == true){{
                    if (radios[i].value==answer){{
                        alert(\"You got it!\");
                    }} else {{
                        alert(\"You get the wrong answer!\");
                    }}
                    break;
                }} 
            }}
        }}

    '''.format(answer=case)
    
    with open(filename, mode="w+", encoding="UTF-8") as f:
        f.write(s.format(music_url,li_str,js_code))


def process_music():
    args = parser.parse_args()
    music_id = parse_share_url(args.link)
    count = read_config()
    download_music(music_id, "{}.mp3".format(count))
    clip_music("{}.mp3".format(count),calculate_time(args.start),calculate_time(args.end),"{}_.mp3".format(count))
    

def send_group_voice_msg(groupid, filename):
    basename = os.path.basename(filename)
    basename_without_extension = basename.split('.')[0]
    shutil.copyfile(filename, "C:\\Users\\Asqura\\Downloads\\CQP-xiaoi\\酷Q Pro\\data\\record\\{}.mp3".format(basename_without_extension))

    playload = {
      'group_id':"{}".format(groupid),
      'message':"[CQ:record,file={}]".format(filename),
      'auto_escape':'false'
    }
    res=requests.get("http://localhost:5700/send_group_msg",params=playload)


def send_qqgroup_voice_msg(groupid):
    count = read_config()
    filename = "{}_.mp3".format(count)
    shutil.copyfile(filename, "C:\\Users\\Asqura\\Downloads\\CQP-xiaoi\\酷Q Pro\\data\\record\\{}_.mp3".format(count))
    
    playload = {
      'group_id':"{}".format(groupid),
      'message':"[CQ:record,file={}]".format(filename),
      'auto_escape':'false'
    }
    res=requests.get("http://localhost:5700/send_group_msg",params=playload)


def send_qqgroup_msg(groupid, msg):
    playload = {
      'group_id':"{}".format(groupid),
      'message':msg,
      'auto_escape':'false'
    }
    res=requests.get("http://localhost:5700/send_group_msg",params=playload)

def send_private_msg(user_id, msg):
    playload = {
      'user_id':"{}".format(user_id),
      'message':msg,
      'auto_escape':'false'
    }
    res=requests.get("http://localhost:5700/send_private_msg",params=playload)


def make_choices_msg():
    args = parser.parse_args()
    answer = args.answer;
    choices = args.choices;
    msg = ""
    labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    answer_index = random.randint(0, len(choices))
    choices.insert(answer_index, answer)
    i = 0

    for choice in choices:
        msg = msg + "{}.{}\n".format(labels[i],choice)
        i = i + 1

    return {
        "msg":msg,
        "index":answer_index
    }


def set_answer(answer):
    playload = {
        'key':answer
    }
    res = requests.post("http://127.0.0.1:5700/set_key",json=playload)

    return res

def start_game():
    res = requests.post("http://127.0.0.1:5700/start_game")
    return res

def get_num_of_tracks():
    conn = sqlite3.connect("tracks.db")
    cursor = conn.cursor()

    c = cursor.execute("SELECT COUNT(*) FROM TRACKS;")
    res = c.fetchone()

    conn.close()

    return res[0]


def get_all_tracks():
    conn = sqlite3.connect("tracks.db")
    cursor = conn.cursor()

    c = cursor.execute("SELECT * FROM TRACKS;")
    res = c.fetchall()

    conn.close()
    return res

def get_track_count():
    conn = sqlite3.connect("tracks.db")
    c = conn.cursor();

    c.execute("SELECT COUNT(*) FROM TRACKS;")
    return c.fetchall()[0][0]

def pick_music_randomly():
    num_of_tracks = get_num_of_tracks()
    index = random.randint(875, 1091)

    tracks = get_all_tracks()
    name = tracks[index][1]
    track_id = tracks[index][5]
    duration_time = tracks[index][4]
    sec = random.randint(8, 25)
    start = random.randint(0, duration_time - sec*1000)
    end = start + sec * 1000

    filename = "{}.mp3".format(track_id)
    target_filename = "{}_.mp3".format(track_id)

    download_music(track_id, "{}.mp3".format(track_id))
    clip_music(filename, start, end, target_filename)

    return (name,track_id,start,end,target_filename)




# def game(groupid):
#     process_music()
#     send_qqgroup_msg(groupid, "Recognize the piece of the tune and select the correct answer.")
#     send_qqgroup_voice_msg(groupid)
#     data = make_choices_msg()
#     msg = data['msg']
#     send_qqgroup_msg(groupid, msg)
#     set_answer(data['index'])
#     start_game()
    
        

# if __name__ == "__main__":
#     init_parser_random_ver()
#     args = parser.parse_args()
#     data = pick_music_randomly()
#     playload = {
#         'name':data[0],
#         'track_id':data[1],
#         'start_time':data[2],
#         'end_time':data[3],
#         'group_id':eval(args.groupid)
#     }
#     requests.post("http://127.0.0.1:5000/set_game_data",json=playload)
#     send_group_voice_msg(args.groupid, data[4])
    
    
    