from flask import Flask, request, abort, g, render_template, redirect, url_for, send_from_directory, session, flash, current_app
import redis
import os
import ConfigParser
import bcrypt
import functools
import sys

from PyChannel import commands
from PyChannel.objects import *
from PyChannel.helpers.channel import *

pychannel_plugins = {}
#import the plugins into the `plugins` dict
channel_path = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(channel_path, "plugins")):
	for file_name in os.listdir(os.path.join(channel_path, "plugins")):
		fname, ext = file_name.rsplit('.', 1)
		if ext == "py" and fname != "__init__":
			print "Adding plug-in:", fname
			mname = ".".join(["PyChannel", "plugins", fname])
			__import__(mname)
			pychannel_plugins[fname] = sys.modules[mname]

app = Flask(__name__)

app.debug = True
app.secret_key = "A Secret Key" #CHANGE THIS!!!
			
def check_redis():
	"Check to see if we can connect to redis"
	r_server = redis.Redis(db="2channel")
	try:
		r_server.ping()
	except redis.ConnectionError, e:
		print "## ERROR: The redis server appears not to be running."
		raise e
	r_server = None #add the redis stuff to the garbage
		
@app.before_request
def setup_globals():
	"Setup the global options."
	g.r = redis.Redis(db="2channel") #Ini Redis
	g.conf = ConfigParser.SafeConfigParser() #Ini the configs
	g.conf.readfp(open("/home/josh/Development/PyChannel/channel.ini"))
	g.env = {}
	g.signals = Signals()
	commands.plug.plug_in()
	for plugin in pychannel_plugins.itervalues():
		plugin.plug.plug_in()
## Custom Errors

class ImageNotFound(Exception):
	pass

## Routes
	
@app.route('/')
def index():
	"Index of the site."
	return render_template("index.html")
	
@app.errorhandler(400)
def error(error):
	"Show general error messages sent via flash()s"
	return render_template("error.html", rd=request.base_url)
	
@app.errorhandler(ImageNotFound)
def no_image(error):
	"Redirect not found images to the image_not_found image."
	return redirect(url_for("static", filename="image_not_found.png"))
	
@app.errorhandler(ImmediateRedirect)
def imm_redirect(error):
	return error.r
	
@app.route("/images/<image_hash>/delete")
def delete_image(image_hash):
	"Removes an image"
	
	if session.get("level"):
		if g.r.get("image:{0}".format(image_hash)):
			image = PostImage.get_from_hash(image_hash)
			g.r.delete("image:{0}".format(image_hash))
			try:
				os.remove(os.path.join(g.conf.get("site", "image_store"), image.url))
				os.remove(os.path.join(g.conf.get("site", "image_store"), "thumb."+image.url))
				g.signals.delete_image.send(current_app._get_current_object(), image=image)
			except OSError:
				flash("No image: {0}".format(image.url))
				abort(400)
		
	return redirect(request.environ.get("HTTP_REFERER", url_for("index")))
	
@app.route('/images/<filename>')
def uploaded_file(filename):
	"Return an uploaded file."
	if not os.path.exists(os.path.join(g.conf.get("site", "image_store"), filename)):
		raise ImageNotFound("Error")
	return send_from_directory(g.conf.get("site", "image_store"), filename)
		
@app.route("/boards/<board>/<int:thread_id>/delete")
def delete_thread(board, thread_id):
	"Remove a thread"
	
	if session.get("level") and g.r.exists("thread:{0}".format(thread_id)):
		Thread.from_id(thread_id).delete()
	
	return redirect(request.environ.get("HTTP_REFERER", url_for("board", board=board)))
	
@app.route("/boards/<board>/<int:thread_id>/image/delete")
def remove_thread_image(board, thread_id):
	"Remove a thread's image without removeing the image on disk"
	
	if session.get("level") and g.r.exists("thread:{0}".format(thread_id)):
		t = Thread.from_id(thread_id)
		delattr(t, "image")
		t.save()
	
	return redirect(request.environ.get("HTTP_REFERER", url_for("board", board=board)))
	
@app.route("/boards/<board>/<int:thread_id>/<int:reply_id>/delete")
def delete_reply(board, thread_id, reply_id):
	"Remove a reply"
	
	if session.get("level") and g.r.exists("reply:{0}".format(reply_id)):
		Reply.from_id(reply_id).delete()
	
	return redirect(request.environ.get("HTTP_REFERER", url_for("board", board=board)))
	
@app.route("/boards/<board>/<int:thread_id>/<int:reply_id>/image/delete")
def remove_reply_image(board, thread_id, reply_id):
	"Remove an image from a reply without deleteing it on disk"
	
	if session.get("level") and g.r.exists("reply:{0}".format(reply_id)):
		r = Reply.from_id(reply_id)
		delattr(r, "image")
		r.save()
	
	return redirect(request.environ.get("HTTP_REFERER", url_for("board", board=board)))

@app.route('/boards/<board>', methods=['POST'])
def post(board):
	"Add a post to the board"
	sec = "{0}:options".format(board)
	if board not in g.conf.options("boards"):
		abort(404)
	elif not get_opt(sec, "allow_threads", True, "bool"):
		flash("Thread creation not allowed.")
		abort(400)
		
	meta = get_post_opts(request.form.get("subject", ""),
						 request.form.get("author", "Anonymous"))
	meta["post"] = Thread(text = request.form["content"],
						  subject = meta["subject"],
						  author = meta["author"],
						  board = board)
		
	g.signals.pre_post.send(current_app._get_current_object(), meta=meta)
	g.signals.new_post.send(current_app._get_current_object(), meta=meta)
		
	meta["post"].save()
	
	g.signals.save_post.send(current_app._get_current_object(), meta=meta)
	
	if get_opt(sec, "prune_threads", True, "bool"):
		Board(board).prune(to_thread_count=get_opt(sec, "prune_threads_after", 250, "int"))
	
	return redirect(url_for("board", board=board))

@app.route('/boards/<board>')
def board(board):
	"Get a board's threads."
	if board not in g.conf.options("boards"):
		abort(404)
		
	page = None
	if get_opt("{0}:options".format(board), "pagination", False, "bool"):
		page = {
			"num": int(request.args.get("page", 0)),
			"per_page": get_opt("{0}:options".format(board), "threads_per_page", 15, "int")
		}
		if page["per_page"] < 1:
			page["per_page"] = 1
		page["thread_start"] = page["num"]*page["per_page"]
		page["thread_stop"] = (page["num"]*page["per_page"])+page["per_page"]-1
		
	return render_template("board.html", board = Board(board), page=page)
		
@app.route('/boards/<board>/<int:thread_id>', methods=['POST'])
def reply(board, thread_id):
	"Post a reply to a thread with thread_id"
	sec = "{0}:options".format(board)
	if board not in g.conf.options("boards") or not g.r.exists("thread:{0}".format(thread_id)):
		abort(404)
	elif not get_opt(sec, "allow_replies", True, "bool"):
		flash("Replies not allowed.")
		abort(400)
		
	meta = get_post_opts(request.form.get("subject", ""),
						 request.form.get("author", "Anonymous"))
	
	meta["post"] = Reply(thread_id,
						 text = request.form["content"],
						 subject = meta["subject"],
						 author = meta["author"],
						 board = board)
		
	#if meta.get("command"):
	#	r = meta["command"](**meta)
	#	if r: return r
		
	g.signals.new_post.send(current_app._get_current_object(), meta=meta) # Send out the new_post signal
	
	meta["post"].save()
	
	g.signals.save_post.send(current_app._get_current_object(), meta=meta)
	
	return redirect(url_for("thread", board=board, thread_id=thread_id))
	
@app.route('/boards/<board>/<int:thread_id>')
def thread(board, thread_id):
	"Retrive a thread"
	if board not in g.conf.options("boards") or not g.r.exists("thread:{0}".format(thread_id)):
		abort(404)
		
	else:
		return render_template("thread.html",
							   board = Board(board),
							   thread = cP.loads(g.r.get("thread:{0}".format(thread_id))))
	
if __name__ != '__main__':
	application  = app #so as to comply with wsgi standards
