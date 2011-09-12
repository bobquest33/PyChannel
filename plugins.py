from PluginHelpers import PluginHandler
from objects import PostImage
from flask import flash, abort, g, request
from ChannelHelpers import get_opt

plug = PluginHandler()
	
@plug.register("new_image")
def new_image_saved(sender, image):
	"Log new images"
	g.r.rpush("image:log", "NEW: '{0}' {1}".format(image.filename, image.id))
	
@plug.register("new_post")
def check_valid(sender, meta):
	"Validates the current post"
	sec = "{0}:options".format(meta["post"].board)
	
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
	elif not image and require_images:
		if meta["post"].is_reply:
			flash("Reply image required for posting.")
		else:
			flash("Thread image required for posting.")
		abort(400)
	