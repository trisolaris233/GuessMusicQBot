import tools.track as track
import tools.netease
from tools.coolq import *
from tools.util import *



def start(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']


	if not check_permission(user_id, group_id, 6):
		at_and_say(user_id, group_id, "Failed to establish a game: Permission DENIED")
		return 0
	args_num = get_args_number(args)
	res = 0
	# 如果有附加参数 则默认认为设置了模式
		# 没有附加参数 直接开始游戏
	if args_num == 0:
		res = establish_game(user_id, group_id)
	if args_num > 0 and args[0].isnumeric():
		mode = int(args[0])
		res = establish_game(user_id, group_id, mode)

	if res == 1:
		at_and_say(user_id, group_id, "You have estabished a *NEW GAME*!")
	elif res == 0:
		at_and_say(user_id, group_id, "Failed to create a GAME: another GAME is running!")

def end(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']

	if not check_permission(user_id, group_id, 6):
		at_and_say(user_id, group_id, "Unable to end current GAME: u LOSER!")
		return 0

	end_game(group_id)
	at_and_say(user_id, group_id, "All games are ended now.")

def info(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']

	args_number = get_args_number(args)

	if args_number > 0:
		lower_str = str.lower(args[0])
		if lower_str == "track" or lower_str == "tracks" :
			at_and_say(user_id, group_id, "There are {} tracks avail".format(track.get_track_count()))
		elif lower_str == "game" or lower_str == "games":
			pass
		elif lower_str == "db":
			pass
	else:
		user = get_user_info(user_id, group_id)
		if not user:
			at_and_say(user_id, group_id, "Failed to get user infomation: You are not in database")
		at_and_say(user_id, group_id, user.tostring())


def insert(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']

	if not check_permission(user_id, group_id, 5):
		at_and_say(user_id, group_id, "Failed to insert: Permission DENIED")
		return

	args_number = get_args_number(args)
	if args_number > 0:
		at_and_say(user_id, group_id, "Starting to insert, please WAIT...")
		res = track.import_from_url(args[0], user_id, group_id, get_arg_or(args, 1, ''))
		if not res:
			at_and_say(user_id, group_id, "Failed to insert: UNKNOWN ERROR")
			return

		at_and_say(user_id, group_id, "Insertion Successful: {} TRACKS loaded!".format(res[-1]))


def search(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']

	if not check_permission(user_id, group_id,4):
		at_and_say(user_id, group_id, "Failed to search: Permission DENIED")
	args_number = get_args_number(args)

	if args_number == 0:
		at_and_say(user_id, group_id, "Argument Error: too less argument to search")
		return

	if args_number == 1 and args[0].isnumeric():
		res = track.search_song_with_id(int(args[0]))
		at_and_say(user_id, group_id, track.output_track_list(res))

	elif args_number == 2 and args[0].isnumeric() and args[1].isnumeric():
		res = track.search_song_with_id(int(args[0]), int(args[1]))
		at_and_say(user_id, group_id, track.output_track_list(res))



CALL_COMMAND = {}
CALL_COMMAND['?start'] = start
CALL_COMMAND['?end'] = end
CALL_COMMAND['?info'] = info
CALL_COMMAND['?ins'] = insert
CALL_COMMAND['?search'] = search