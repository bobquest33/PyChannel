from flask import Flask, request, abort, g, render_template, redirect, \
				  url_for, send_from_directory, session, flash, \
				  current_app, make_response
import redis
import os
import ConfigParser
import bcrypt
import functools
import sys
from datetime import timedelta

from PyChannel import commands
from PyChannel.helpers.channel import *
from PyChannel.objects import *

from PyChannel.helpers.plugin import ImmediateRedirect

from PyChannel.config import Config

#plugins

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

def parse_board(func):
	
	@functools.wraps(func)
	def wrapper(board=None, *args, **kwargs):
		if board:
			board = g.conf.boards.get(str(board))
			if board == None: abort(404)
		return func(board=board, *args, **kwargs)
		
	return wrapper
	
def parse_board_thread(func):
	
	@functools.wraps(func)
	@parse_board
	def wrapper(board=None, thread=None, *args, **kwargs):
		if thread:
			try: thread = Thread.from_id(thread)
			except: abort(404)
		return func(board=board, thread=thread, *args, **kwargs)
	return wrapper

@app.before_request
def setup_globals():
	"Setup the global options."
	g.r = redis.Redis(db="2channel") #Ini Redis
	
	g.conf = Config(open("/Users/Joshkunz/Development/PyChannel/pychannel.conf"))
	
	g.env = {}
	g.signals = Signals()
	g.AdminRedirect = lambda board: request.environ.get("HTTP_REFERER", url_for("board", board=board.short))
	
	commands.plug.plug_signals()
	commands.plug.plug_in()
	
	for plugin in pychannel_plugins.itervalues(): plugin.plug.plug_signals()
	for plugin in pychannel_plugins.itervalues(): plugin.plug.plug_in()

## Custom Errors

class ImageNotFound(Exception):
	pass
	
#Errors
	
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

@app.errorhandler(redis.ConnectionError)
def RedisConnectionError(error):
	flash("Redis Connection Error:")
	flash(str(error))
	return render_template("error.html", rd=request.base_url)
	
@app.errorhandler(IOError)
def PIL_IOError(error):
	flash("Error parsing image, probably not a valid image file...")
	return render_template("error.html", rd=request.base_url)

#General Utilities

@app.route('/images/<filename>')
def uploaded_file(filename):
	"Return an uploaded file."
	if not os.path.exists(os.path.join(g.conf.ImageStore, filename)):
		raise ImageNotFound("Error")
	return send_from_directory(g.conf.ImageStore, filename)
	
@app.route('/')
def index():
	"Index of the site."
	size_sorted = [p for p, z in sorted(g.conf.boards.items(),
										key=lambda x: len(x[1]),
										reverse=True)]
	return render_template("index.html", size_sorted=size_sorted)

#Admin

@app.route("/ban/<ipaddress>")
def ban_address(ipaddress):
	if session.get("level"):
		g.r.set(":".join(["ban", ipaddress]), True)
		g.r.expire(":".join(["ban", ipaddress]), int(timedelta(weeks=1).total_seconds()))
	return redirect(request.environ.get("HTTP_REFERER", url_for("index")))
	
@app.route("/images/<image_hash>/delete")
def delete_image(image_hash):
	"Removes an image"
	
	if not session.get("level"): abort(403)
	
	try:
		image = PostImage.get_from_hash(image_hash)
	except TypeError:
		flash("No record for image: {0}".format(image_hash))
		abort(400)
		
	#remove the image's record
	g.r.delete("image:{0}".format(image_hash))
	try:
		os.remove(os.path.join(g.conf.ImageStore, image.url)) 			#delete the Image
		os.remove(os.path.join(g.conf.ImageStore, "thumb."+image.url))  #delete the Thumb
		g.signals.delete_image.send(current_app._get_current_object(), image=image)
	except OSError:
		flash("No image file for: {0}".format(image.url))
		abort(400)
		
	return redirect(request.environ.get("HTTP_REFERER", url_for("index")))
		
@app.route("/boards/<board>/<int:thread>/delete")
@parse_board_thread
def delete_thread(board, thread):
	"Remove a thread"
	if session.get("level"):
		thread.delete()
	
	return redirect(g.AdminRedirect(board))
	
@app.route("/boards/<board>/<int:thread>/image/delete")
@parse_board_thread
def remove_thread_image(board, thread):
	"Remove a thread's image without removing the image on disk"
	
	if session.get("level"):
		delattr(thread, "image")
		thread.save()
	
	return redirect(g.AdminRedirect(board))
	
@app.route("/boards/<board>/<int:thread>/<int:reply_id>/delete")
@parse_board_thread
def delete_reply(board, thread, reply_id):
	"Remove a reply"
	
	if session.get("level") and g.r.exists("reply:{0}".format(reply_id)):
		Reply.from_id(reply_id).delete()
	
	return redirect(g.AdminRedirect(board))
	
@app.route("/boards/<board>/<int:thread>/<int:reply_id>/image/delete")
@parse_board_thread
def remove_reply_image(board, thread, reply_id):
	"Remove an image from a reply without deleteing it on disk"
	
	if session.get("level") and g.r.exists("reply:{0}".format(reply_id)):
		r = Reply.from_id(reply_id)
		delattr(r, "image")
		r.save()
	
	return redirect(g.AdminRedirect(board))

#Board

@app.route('/boards/<board>', methods=['POST'])
@parse_board
def post(board):
	"Add a post to the board"
	
	#Make Sure threads are enabled
	if "Threads" in board.Disable:
		flash("Thread creation not allowed.")
		abort(400)
	
	#Parse out the options
	meta = get_post_opts(request.form.get("subject", ""),
						 request.form.get("author", "Anonymous"))
	
	#Make the new thread Object
	meta["post"] = Thread(text = request.form["content"],
						  subject = meta["subject"],
						  author = meta["trip"],
						  board = board)
	
	#Run signals
	g.signals.execute_commands.send(current_app._get_current_object(), meta=meta)
	g.signals.new_post.send(current_app._get_current_object(), meta=meta)
		
	#Save the post
	meta["post"].save()
	
	#Singal After the post is saved
	g.signals.save_post.send(current_app._get_current_object(), meta=meta)
	
	#Prune the boards
	if board.PruneAt:
		Board(board).prune(to_thread_count=board.PruneAt)
	
	return redirect(url_for("board", board=board.short))

@app.route('/boards/<board>')
@parse_board
def board(board):
	"Get a board's threads."
	page = None
	
	print g.conf.structure.__dict__
	print board.Pagination
	print board._catagory.__dict__
	
	if board.pagination:
		
		print "Running paging code..."
		page = {
			"num": int(request.args.get("page", 0)),
			"per_page": board.PageAt
		}
		if page["per_page"] < 1:
			page["per_page"] = 1
		page["thread_start"] = page["num"]*page["per_page"]
		print page["num"]
		print page["per_page"]
		page["thread_stop"] = (page["num"]*page["per_page"])+page["per_page"]-1
	
	return render_template("board.html", board = board, page=page)

#Thread

@app.route('/boards/<board>/<int:thread>', methods=['POST'])
@parse_board_thread
def reply(board, thread):
	"Post a reply to a thread with thread_id"
	if "Replies" in board.Disable:
		flash("Replies not allowed.")
		abort(400)
		
	meta = get_post_opts(request.form.get("subject", ""),
						 request.form.get("author", "Anonymous"))
	
	meta["post"] = Reply(thread.id,
						 text = request.form["content"],
						 subject = meta["subject"],
						 author = meta["trip"],
						 board = board)
		
	g.signals.execute_commands.send(current_app._get_current_object(), meta=meta)
	g.signals.new_post.send(current_app._get_current_object(), meta=meta) # Send out the new_post signal
	
	meta["post"].save()
	
	g.signals.save_post.send(current_app._get_current_object(), meta=meta)
	
	return redirect(url_for("thread", board=board.short, thread=thread.id))
	
@app.route('/boards/<board>/<int:thread>')
@parse_board_thread
def thread(board, thread):
	"Retrive a thread"
	return render_template("thread.html",
						   board = board,
						   thread = thread)
