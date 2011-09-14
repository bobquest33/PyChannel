from PluginHelpers import PluginHandler
from ChannelHelpers import ImmediateRedirect, get_opt
from flask import redirect, session, request, g, flash, abort
import bcrypt
import functools
from objects import Thread
import time

plug = PluginHandler()

def require(*rargs):
	"A Decorator to allow a command to require certain meta information..."
	def decorator(func):
		@functools.wraps(func)
		def wrapper(sender, meta):
			if meta.get("post") and not get_opt("{0}:commands".format(meta["post"].board), meta["command"], True, "bool"):
				raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
			if not meta.get("command") or not meta["command"] == func.__name__:
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
		raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
		
@plug.register("new_post")
@require("trip", "author_line")
def cpass(sender, meta):
		if (session.get("level") == "mod" and session.get("user") == meta["trip"].username) or\
		session.get("level") == "admin":
			meta["trip"].set_pass(author_line.rsplit("#", 1)[1])
			meta["trip"].save()
		raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
		
@plug.register("new_post")
@require("post")
def asa(cls, meta):
		if session.get("level"):
			meta["post"].capcode = "## {0} ##".format(session.get("level").capitalize())
			
@plug.register("new_post")
@require("post")
def sage(cls, meta):
		if meta["post"].is_reply: g.env["sage"] = True
		
@plug.register("new_post")
@require("post")
def bump(sender, meta):
		if meta["post"].is_reply:
			thread = Thread.from_id(meta["post"].thread)
			if not hasattr(thread, "auto_bump"): thread.auto_bump = 0
			thread.auto_bump += 1
			if thread.auto_bump <= get_opt("{0}:options".format(meta["post"].board), "auto_bump_limit", 200, "int"):
				thread.save()
			else:
				flash("Auto bump limit reached.")
				abort(400)
			
		raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
		
@plug.register("new_post")
@require("post")
def sticky(sender, meta):
	if not session.get("level"): raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
	if meta["post"].is_reply: 
		thread = Thread.from_id(meta["post"].thread)
	else:
		thread = meta["post"]
		
	thread.sticky = True
	thread.save(score=int(time.time())*2)
	plug.fire("lock_thread", thread=thread)
	if meta["post"].is_reply:
		raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
		
@plug.register("new_post")
@require("post")
def unsticky(sender, meta):
	if not session.get("level"): raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
	if meta["post"].is_reply:
		thread = Thread.from_id(meta["post"].thread)
	else:
		thread = meta["post"]
		
	thread.sticky = False
	thread.save()
	plug.fire("unlock_thread", thread=thread)
	if meta["post"].is_reply:
		raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
	