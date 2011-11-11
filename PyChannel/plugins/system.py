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
	
	if not meta["post"].text:
		flash("Post has no contents...")
		abort(400)
	
	require_subject = "ReplySubject" in meta["post"].board.Require if meta["post"].is_reply else "ThreadSubject" in meta["post"].board.Require
	require_author = "ReplyAuthor" in meta["post"].board.Require if meta["post"].is_reply else "ThreadAuthor" in meta["post"].board.Require
	require_content = "ReplyContent" in meta["post"].board.Require if meta["post"].is_reply else "ThreadContent" in meta["post"].board.Require
	
	if require_subject and not meta["post"].subject:
		flash("Reply subject required.") if meta["post"].is_reply else flash("Thread subject required.")
		abort(400)
	
	if require_author and not meta["post"].author:
		flash("Reply author name required.") if meta["post"].is_reply else flash("Thread author required.")
		abort(400)
		
	if require_content and not meta["post"].text:
		flash("Reply content name required.") if meta["post"].is_reply else flash("Thread content required.")
		abort(400);
		
	if meta["post"].is_reply and meta["post"].board.ReplyLimit and \
	len(Thread.from_id(meta["post"].thread)) >= meta["post"].board.ReplyLimit:
		flash("Reply limit reached...")
		abort(400)
		
@plug.register("new_post")
def check_image(sender, meta):
	"Checks to see if an image is included and then saves it."
	image = request.files.get("image", None)
	
	allow_images = "ReplyImage" not in meta["post"].board.Disable if meta["post"].is_reply else "ThreadImage" not in meta["post"].board.Disable
	require_images = "ReplyImage" not in meta["post"].board.Require if meta["post"].is_reply else "ThreadImage" not in meta["post"].board.Require
	
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