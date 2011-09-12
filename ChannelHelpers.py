from flask import g

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