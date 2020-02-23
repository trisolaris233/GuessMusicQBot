import tools.track as track
import sqlite3
import json
import re

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
			winrate = round(game_played/wins * 100,0)
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
		return reg_user(user_id, group_id)

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
	cursor.execute("INSERT INTO GAMEDATA(STATUS, GROUP_ID, MODE, MEMBERS, START_TIME) VALUES(?,?,?,?,?)",
		(0, group_id, mode, json.dumps([user_id]), track.get_strf_local_time()))

	conn.commit()
	conn.close()
	return 1


def end_game(group_id):
	conn = sqlite3.connect(track.server_db_path)
	cursor = conn.cursor()

	cursor.execute("UPDATE GAMEDATA SET STATUS=1 WHERE STATUS=0 AND GROUP_ID=?",(group_id,))
	conn.commit()
	conn.close()