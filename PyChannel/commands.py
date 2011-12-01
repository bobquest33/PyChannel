from flask import redirect, session, request, g, flash, abort, url_for
import time

from PyChannel.helpers.command import require
from PyChannel.helpers.plugin import PluginHandler, ImmediateRedirect
from PyChannel.objects import Thread, Tripcode
from PyChannel.helpers.channel import get_opt

plug = PluginHandler()

#Add the signals defined in command
plug.signal("lock_thread")
plug.signal("unlock_thread")

plug.signal("user_logged_on")
plug.signal("user_registered")
plug.signal("user_changed_password")

@plug.register("execute_commands")
@require("trip")
def login(sender, meta):
	print "Running login..."
	if meta["trip"].permission:
		session["level"] = meta["trip"].permission
		session["user"] = meta["trip"].username
		plug.fire("user_logged_on", user=meta["trip"])
	raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
		
@plug.register("execute_commands")
@require()
def logout(sender, meta):
		if session.get("level"):
			map(session.pop, ("level", "user"))
		raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
		
@plug.register("execute_commands")
@require("trip")
def regi(sender, meta):
	if session.get("level") == "admin":
		meta["trip"].permission = meta["post"].text.strip()
		meta["trip"].save()
		plug.fire("user_registered", user=meta["trip"])
	raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
		
@plug.register("execute_commands")
@require("trip", "author_line")
def cpass(sender, meta):
	if (session.get("level") == "mod" and session.get("user") == meta["trip"].username) or session.get("level") == "admin":
		meta["trip"].password = author_line.rsplit("#", 1)[1]
		meta["trip"].save()
		plug.fire("user_changed_password", user=meta["trip"])
	raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
	
@plug.register("execute_commands")
@require()
def unban(sender, meta):
	if session.get("level"):
		address = meta["post"].text.strip()
		if g.r.exists(":".join(["ban", address])):
			g.r.delete(":".join(["ban", address]))
	raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
		
@plug.register("execute_commands")
@require("post")
def asa(cls, meta):
	if session.get("level"):
		meta["post"].capcode = "## {0} ##".format(session.get("level").capitalize())
			
@plug.register("execute_commands")
@require("post")
def sage(cls, meta):
	if meta["post"].is_reply: g.env["sage"] = True
		
@plug.register("execute_commands")
@require("post")
def bump(sender, meta):
	if meta["post"].is_reply:
		thread = Thread.from_id(meta["post"].thread)
		if not hasattr(thread, "auto_bump"): thread.auto_bump = 0
		thread.auto_bump += 1
		if thread.auto_bump <= meta["post"].board.AutoBump:
			thread.save()
		else:
			flash("Auto bump limit reached.")
			abort(400)
		raise ImmediateRedirect(redirect(url_for("board", board=str(thread.board) )))
			
	raise ImmediateRedirect(redirect(request.http_referer))
		
@plug.register("execute_commands")
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
		
@plug.register("execute_commands")
@require("post")
def unsticky(sender, meta):
	if not session.get("level"): raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
	if meta["post"].is_reply:
		thread = Thread.from_id(meta["post"].thread)
	else:
		thread = meta["post"]
		
	thread.sticky = False
	thread.save(score=int(time.time()))
	plug.fire("unlock_thread", thread=thread)
	if meta["post"].is_reply:
		raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
	