from flask import flash, abort, g, request
from PyChannel.helpers.plugin import PluginHandler

plug = PluginHandler()
	
@plug.register("new_image")
def new_image_saved(sender, image):
	"Log new images"
	print "New Image!", image.filename
	g.r.rpush("image:log", "NEW: '{0}' {1}".format(image.filename, image.id))
	