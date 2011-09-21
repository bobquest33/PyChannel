from flask import flash, abort, g, request
from datetime import timedelta
from PyChannel.objects import Thread, PostImage
from PyChannel.helpers.channel import get_opt
from PyChannel.helpers.plugin import PluginHandler

plug = PluginHandler()

@plug.register("execute_commands")
def check_ban(sender, meta):
	"Checks to see if a user has an outstanding ban..."
	if g.r.exists(":".join(["ban", request.remote_addr])):
		remaining = g.r.ttl(":".join(["ban", request.remote_addr]))
		r_sec = remaining%60
		remaining /= 60
		r_min = remaining%60
		remaining /= 60
		r_hou = remaining%24
		r_day = remaining/24
		flash("There is currently a ban on this address.")
		flash("{0} day(s) {1:0>2}:{2:0>2}:{3:0>2} Remaining...".format(r_day, r_hou, r_min, r_sec))
		abort(400)

@plug.register("new_post")
def check_valid(sender, meta):
	"Validates the current post"
	sec = "{0}:options".format(meta["post"].board)
	
	if not meta["post"].text:
		flash("Post has no contents...")
		abort(400)
	
	require_subject = get_opt(sec, "require_reply_subject", False, "bool") if meta["post"].is_reply else get_opt(sec, "require_thread_subject", False, "bool")
	require_author = get_opt(sec, "require_reply_author", False, "bool") if meta["post"].is_reply else get_opt(sec, "require_thread_author", False, "bool")
	
	if require_subject and not meta["post"].subject:
		flash("Reply subject required.") if meta["post"].is_reply else flash("Thread subject required.")
		abort(400)
	
	if require_author and not meta["post"].author:
		flash("Reply author name required.") if meta["post"].is_reply else flash("Thread author required.")
		abort(400);
		
	if meta["post"].is_reply and get_opt(sec, "enable_reply_limit", False, "bool") and \
	len(Thread.from_id(meta["post"].thread)) >= get_opt(sec, "reply_limit", 1000, "int"):
		flash("Reply limit reached...")
		abort(400)
		
@plug.register("new_post")
def check_image(sender, meta):
	"Checks to see if an image is included and then saves it."
	sec = "{0}:options".format(meta["post"].board)
	image = request.files.get("image", None)
	allow_images = get_opt(sec, "allow_reply_images", True, "bool") if meta["post"].is_reply else get_opt(sec, "allow_thread_images", True, "bool")
	require_images = get_opt(sec, "require_reply_image", False, "bool") if meta["post"].is_reply else get_opt(sec, "require_thread_image", False, "bool")
	if allow_images and image:
		meta["post"].image = PostImage(image)
		meta["post"].image.save()
		if not hasattr(meta["post"].image, "resolution"):
			flash("Not a valid Image.")
			abort(400)
	elif not image and require_images:
		if meta["post"].is_reply:
			flash("Reply image required for posting.")
		else:
			flash("Thread image required for posting.")
		abort(400)