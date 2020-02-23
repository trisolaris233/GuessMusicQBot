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
		elif lower_str.isnumeric():
			user = get_user_info(int(lower_str), group_id)
			if not user:
				at_and_say(user_id, group_id, "Failed to get user infomation: *404 NOT FOUND!*")
			at_and_say(user_id, group_id, user.tostring())
	else:
		user = get_user_info(user_id, group_id)
		if not user:
			at_and_say(user_id, group_id, "Failed to get user infomation: *404 NOT FOUND*")
		at_and_say(user_id, group_id, user.tostring())


def insert(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']

	if not check_permission(user_id, group_id, 5):
		at_and_say(user_id, group_id, "Failed to insert: Permission DENIED")
		return

	args_number = get_args_number(args)
	if args_number > 0:
		at_and_say(user_id, group_id, "Starting to insert, please WAIT... ")
		res = track.import_from_url(''.join(args), user_id, group_id)

		if not res:
			at_and_say(user_id, group_id, "Failed to insert: UNKNOWN ERROR")
			return

		at_and_say(user_id, group_id, "Insertion Successful: {} TRACKS inserted, ID ranges form[{},{}]".format(res[1], res[0],res[0] + res[1] - 1))

	else:
		at_and_say(user_id, group_id, "Argument ERROR: too less argument")

'''
关于search的模式 有以下几种
0 按id搜索
1 按track id搜索
2 按name搜索
3 按artist搜索
4 按album搜索
5 按插入者搜索
'''
def search(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']
	args_number = get_args_number(args)

	if not check_permission(user_id, group_id, 4):
		at_and_say(user_id, group_id, "Failed to search: Permission DENIED")

	if args_number == 0:
		at_and_say(user_id, group_id, "Argument ERROR: too less argument")

	if args_number == 1:
		if args[0] == "help":
			send_group_msg(group_id,'''
			Command srh: Search tracks with specified argument in the database.
			Permission requirecd: 4
			Usage: ?srh Mode Field1 [Fields...]
			Mode:
			0 Search With ID
			1 Search With Name of Tracks
			3 Search With Name of Artist(s)
			4 Search With Name of Ablum
			5 Search With QQ of who insert the track*(not supported yet)

			example:
				?srh 1 上海 -> Output tracks which's names contain "上海"
				?srh 0 203 -> Output tracks ID ranges [203,inf]
				?srh 0 203 204 -> Output tracks ID ranges from[203,204]
		''')
			return
		elif not args[0].isnumeric():
			at_and_say(user_id, group_id, "Argument Error: Invalid argument")



	mode = int(args[0])
	'''

	模式1 按id进行搜索

	'''
	if mode == 0:
		if not args[1].isnumeric():
			at_and_say(user_id, group_id, "Argument Error: Invalid argument")
			return

		arg2 = get_arg_or(args,2,None)
		if arg2 and arg2.isnumeric():
			res = track.search_song_with_id(int(args[1]), int(arg2))
			at_and_say(user_id, group_id, "\n"+track.output_track_list(res))
			return
		elif not arg2:
			res = track.search_song_with_id(int(args[1]))
			at_and_say(user_id, group_id,"\n"+track.output_track_list(res))
			return
		else:
			at_and_say(user_id, group_id, "Argument Error: Invalid argument")
			return

		
	'''

	模式2 按track_id进行搜索
	
	'''
	if mode == 1:
		if not args[1].isnumeric():
			at_and_say(user_id, group_id, "Argument Error: Invalid argument")
			return
		res = track.search_song_with_track_id(int(args[1]))
		at_and_say(user_id, group_id, "\n"+track.output_track_list(res))


	'''

	模式3 按name进行搜索
	
	'''
	if mode == 2:
		res = track.search_song_with_name(args[1])
		at_and_say(user_id, group_id, "\n"+track.output_track_list(res))

	'''

	模式3 按artist_name进行搜索
	
	'''
	if mode == 3:
		res = track.search_song_with_artist_name(args[1])
		at_and_say(user_id, group_id, "\n"+track.output_track_list(res))

	'''

	模式4 按album_name进行搜索
	
	'''
	if mode == 4:
		res = track.search_song_with_album_name(args[1])
		at_and_say(user_id, group_id, "\n"+track.output_track_list(res))

	# elif mode == 5:
	# 	if not args[1].isnumeric():
	# 		at_and_say(user_id, group_id, "Argument Error: Invalid argument")
	# 		return
	# 	res = track.search_song_with_operator(int(args[1]))
	# 	at_and_say(user_id, group_id, "\n"+track.output_track_list(res))


def rm(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']

	if not check_permission(user_id, group_id, 6):
		at_and_say(user_id, group_id, "Failed to REMOVE: Permission DENIED")
	args_number = get_args_number(args)

	if args_number == 0:
		at_and_say(user_id, group_id, "Argument Error: too less argument")
		return

	if not args[0].isnumeric():
		at_and_say(user_id, group_id, "Argument Error: Invalid argument")

	arg2 = get_arg_or(args,1,None)
	if arg2 and arg2.isnumeric():
		res = track.remove_track_with_id(int(args[0]), int(arg2), user_id, group_id)
		at_and_say(user_id, group_id, "\nthese TRACKS are DELETED:\n"+track.output_track_list(res))
		return
	elif not arg2:
		res = track.remove_track_with_id(int(args[0]), -1, user_id, group_id)
		at_and_say(user_id, group_id, "\nthese TRACKS are DELETED:\n"+track.output_track_list(res))
		return
	else:
		at_and_say(user_id, group_id, "Argument Error: Invalid argument")
		return





CALL_COMMAND = {}
CALL_COMMAND['?start'] = start
CALL_COMMAND['?end'] = end
CALL_COMMAND['?info'] = info
CALL_COMMAND['?ins'] = insert
CALL_COMMAND['?srh'] = search
CALL_COMMAND['?rm'] = rm