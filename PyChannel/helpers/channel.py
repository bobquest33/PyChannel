from flask import g
from PyChannel.objects import Tripcode

class ImmediateRedirect(Exception):
	"Immediately Redirect a request"
	
	def __init__(self, redirect_object):
		self.r = redirect_object

def get_opt(section, option, default=None, type="str"):
	"Get a config option. Auto checks for aproprite[sp] sections and options."
	get_types = {
		"str": g.conf.get,
		"bool": g.conf.getboolean,
		"int": g.conf.getint,
		"float": g.conf.getfloat
	}
	if not g.conf.has_section(section):
		return default
	elif not g.conf.has_option(section, option):
		return default
	return get_types[type](section, option)
	
def get_post_opts(subject_line, author_line):
	"Parses out the commands and passwords from the subject and autor lines of a post"
	
	meta = {
		"subject_line": subject_line,
		"author_line": author_line
	}
	
	sl = subject_line.rsplit(get_opt("site", "command_sep", "#!"), 1)
	meta["subject"] = sl[0]
	if len(sl) > 1: meta["command"] = sl[1]
	
	al = author_line.rsplit("#", 1)
	meta["author"] = al[0]
	if len(al) > 1: meta["trip"] = Tripcode(meta["author"], al[1])
	
	return meta