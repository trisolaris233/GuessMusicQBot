import requests


def send_group_voice_msg(groupid, filename, coolq_record_dir):
    basename = os.path.basename(filename)
    basename_without_extension = basename.split('.')[0]
    shutil.copyfile(filename, coolq_record_dir + "{}.mp3".format(basename_without_extension))

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