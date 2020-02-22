
import requests
import json
import sys
from urllib.parse import urlparse
from urllib.parse import parse_qs
import re
from pydub import AudioSegment
import argparse
import random

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


def read_config():
    count = 0
    try:
        with open("cofig.txt", "r+") as f:
            count = eval(f.read())
    except FileNotFoundError:
        write_config(0)
        count = 0
    return count

def write_config(count):
    with open("config.txt", "w+") as f:
        f.write(str(count))

def update_config():
    count = read_config()
    write_config(count+1)


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
        s = f.read();
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


def main_process():
    music_id = parse_share_url(args.link)
    download_music(music_id)
    clip_music("{}.mp3".format(music_id),calculate_time(args.start),calculate_time(args.end),"{}_.mp3".format(music_id))

if __name__ == "__main__":
    init_parser()
    args = parser.parse_args()
    music_id = parse_share_url(args.link)
    count = read_config()
    download_music(music_id, "{}.mp3".format(count))
    clip_music("{}.mp3".format(count),calculate_time(args.start),calculate_time(args.end),"{}_.mp3".format(count))
    generate_html("{}_.mp3".format(count),args.answer,args.choices,"{}.html".format(count))
    
    
    