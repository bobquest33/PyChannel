from PluginHelpers import PluginHandler
from ChannelHelpers import ImmediateRedirect
from flask import redirect, session, request, g
import bcrypt
import functools

plug = PluginHandler()

def require(*rargs):
	"A Decorator to allow a command to require certain meta information..."
	def decorator(func):
		@functools.wraps(func)
		def wrapper(sender, meta):
			if not meta["command"] or not meta["command"] == func.__name__:
				return None
			for a in rargs:
				if a not in meta:
					raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
			return func(sender, meta)
		return wrapper
	return decorator

@plug.register("new_post")
@require("trip", "author_line")
def login(sender, meta):
	if meta["trip"].get_level() in ["admin", "mod"] and \
		bcrypt.hashpw(meta["author_line"].rsplit("#", 1)[1], meta["trip"].passwd) == meta["trip"].passwd:
			print "Password Taken"
			session["level"] = meta["trip"].get_level()
			session["user"] = meta["trip"].username
			raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
		
@plug.register("new_post")
@require()
def logout(sender, meta):
		if session.get("level"):
			map(session.pop, ("level", "user"))
		raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
		
@plug.register("new_post")
@require("trip")
def regi(sender, meta):
		if session.get("level") == "admin":
			meta["trip"].set_permission(level)
			meta["trip"].save()
		return ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
		
@plug.register("new_post")
@require("trip", "author_line")
def cpass(sender, meta):
		if (session.get("level") == "mod" and session.get("user") == meta["trip"].username) or\
		session.get("level") == "admin":
			meta["trip"].set_pass(author_line.rsplit("#", 1)[1])
			meta["trip"].save()
		return ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
		
@plug.register("new_post")
@require("post")
def asa(cls, meta):
		if session.get("level"):
			meta["post"].capcode = "## {0} ##".format(session.get("level").capitalize())
			
@plug.register("new_post")
@require("post")
def sage(cls, meta):
		if meta["post"].is_reply: g.env["sage"] = True
		
@plug.register("save_post")
@require("post")
def bump(sender, meta):
		if meta["post"].is_reply:
			Thread.bump_thread(post.board, post.thread)
		return ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))