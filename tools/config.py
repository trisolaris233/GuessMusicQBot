import tools.track as track
import tools.netease
from tools.coolq import *
from tools.util import *

def guess_checker(msg):
	if msg.startswith("guess"):
		return 0
	return -1

def parse_guess(msg):
	return [msg[:5], msg[6:]]


def reg(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']

	if get_user_info(user_id, group_id):
		at_and_say(user_id, group_id, "You've already registered")
		return

	res = reg_user(user_id, group_id)
	if res == 0:
		at_and_say(user_id, group_id, "Registeration Failed: UNKNOWN ERROR")
		return
	at_and_say(user_id, group_id, "Registeration Successful: Your ID:{}".format(res))

def start(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']


	if not check_permission(user_id, group_id, 6):
		at_and_say(user_id, group_id, "Failed to establish a game: Permission DENIED")
		return 0
	args_num = get_args_number(args)
	res = 0
	mode = 0
	# 如果有附加参数 则默认认为设置了模式
		# 没有附加参数 直接开始游戏
	if args_num == 0:
		res = establish_game(user_id, group_id)
	if args_num > 0 and args[0].isnumeric():
		mode = int(args[0])
		res = establish_game(user_id, group_id, mode)

	if res == 1:
		start_game(group_id, mode)
		game = get_games_established(group_id)[0]
		send_group_msg(group_id, "Game started, gid={} mode={}".format(game[0],game[3]))
		return

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
		elif lower_str == "cur" or lower_str == "cursor":
			res = get_cursor_range()
			length = len(res)

			if length == 0:
				at_and_say(user_id, group_id, "cursor ranges all")
			elif length < 8:
				at_and_say(user_id, group_id, json.dumps(res))
			else:
				at_and_say(user_id, group_id, "There're {} tracks in cursor's range.".format(length))
		elif lower_str == "db":
			pass
		elif lower_str.isnumeric():
			user = get_user_info(int(lower_str), group_id)
			if not user:
				at_and_say(user_id, group_id, "Failed to get user infomation: *404 NOT FOUND!*")
			at_and_say(user_id, group_id, user.tostring())


		s = parse_cq_code(args[0])
		if s and s[0].lower() == 'at' and s[1].lower() == 'qq' and s[2].isnumeric():
			user = get_user_info(int(s[2]), group_id)
			if not user:
				at_and_say(user_id, group_id, "Failed to get user infomation: *404 NOT FOUND!*")
			at_and_say(user_id, group_id, user.tostring())
	else:
		user = get_user_info(user_id, group_id)
		if not user:
			at_and_say(user_id, group_id, "Failed to get user infomation: *404 NOT FOUND*")
			return
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

def search(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']
	args_number = get_args_number(args)
	print("args number = ", args_number)
	mode = 0
	modes_string = {
		'id':0,
		'tid':1,
		'name':2,
		'ar':3,
		'al':4,
		'qq':5
	}

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
			0|id Search With ID
			1|tid Search With Track ID, which is known in url
			2|name Search With Name of Tracks
			3|ar Search With Name of Artist(s)
			4|al Search With Name of Ablum
			5|qq Search With QQ of who insert the track*(not supported yet)

			example:
				?srh 1 上海 -> Output tracks which's names contain "上海"
				?srh 0 203 -> Output tracks ID ranges [203,inf]
				?srh 0 203 204 -> Output tracks ID ranges from[203,204]
		''')
			return

	if not args[0].isnumeric():
		try:
			mode = modes_string[args[0].lower()]
		except:
			at_and_say(user_id, group_id, "Failed: Invalid Argument")
			return
	else:
		mode = int(args[0])

	
	'''

	模式1 按id进行搜索

	'''
	if mode == 0:

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

def guess(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']
	players = get_game_current_member_list(group_id)
	if not players:
		return
	if not user_id in players:
		join_in_game(user_id, group_id)

	gamedata = get_games_established(group_id)[0]
	track_id = gamedata[4]
	mode = gamedata[3]
	track_info = track.search_song_with_track_id(track_id)[0]
	key_name = track_info[1].lower()
	key_artist_name = track_info[2].lower()
	key_album_name = track_info[3].lower()

	if mode == 0:
		if key_name == args:
			at_and_say(user_id, group_id, "Perfect match!")
			end_game(group_id, user_id)
		elif args in key_name:
			at_and_say(user_id, group_id, "You matched part of it!")

		elif args == key_artist_name:
			at_and_say(user_id, group_id, "you matched artist of it!")

		elif args in key_artist_name:
			at_and_say(user_id, group_id, "You matched part of its artist's name")

		else:
			at_and_say(user_id, group_id, "Wrong Answer, try again")

	elif mode == 1:
		lyric = get_key_lyrics(group_id)
		if args.lower() == lyric.lower():
			at_and_say(user_id, group_id, "Perfect match!")
			end_game(group_id, user_id)
		elif args.lower() in lyric.lower():
			at_and_say(user_id, group_id, "You match part of it")
		else:
			at_and_say(user_id, group_id, "Wrong answer, try again")


def chper(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']

	try:
		target_id = args[0]
		s = parse_cq_code(target_id)
		if s and s[0].lower() =='at' and s[1].lower() =='qq' and s[2].isnumeric():
			target_id = int(s[2])
		permission = args[1]
	except keyError:
		at_and_say(user_id, group_id, "Failed: too less argument")

	user = get_user_info(user_id, group_id)
	current_per = user.permission
	target = get_user_info(target_id, group_id)
	if not target:
		at_and_say(user_id, group_id, "Failed to change PERMISSION: unregistered target")
		return
	if int(permission) < current_per:
		change_permission(target_id, group_id, permission)
		at_and_say(user_id, group_id, "OPERATION successful")
	else:
		at_and_say(user_id, group_id, "Failed to change PERMISSION: permission denied")

def edt(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']

	if not check_permission(user_id, group_id, 6):
		at_and_say(user_id, group_id, "Failed: Permission DENIED")
		return

	tid = 0
	name = ""
	try:
		tid = args[0]
		name = args[1]
	except:
		at_and_say(user_id, group_id, "Failed: too less argument")

	edit_track_name(tid, name)
	at_and_say(user_id, group_id, "OPERATION Successful")

def disable(args, post_msg):
	user_id = post_msg['user_id']
	group_id = post_msg['group_id']

	if not check_permission(user_id, group_id, 6):
		at_and_say(user_id, group_id, "Failed: Permission DENIED")
		return
	pass

def enable(args, post_msg):
	pass

filters = []
filters.append(guess_checker)

cos_parse_msg = []
cos_parse_msg.append(parse_guess)

CALL_COMMAND = {}
CALL_COMMAND['?reg'] = reg
CALL_COMMAND['?start'] = start
CALL_COMMAND['?end'] = end
CALL_COMMAND['?info'] = info
CALL_COMMAND['?ins'] = insert
CALL_COMMAND['?srh'] = search
CALL_COMMAND['guess'] = guess
CALL_COMMAND['?chper'] = chper
CALL_COMMAND['?edt'] = edt
CALL_COMMAND['?disable'] = disable
CALL_COMMAND['?enable'] = enable
# 禁术 rm 不可使用
# CALL_COMMAND['?rm'] = rm