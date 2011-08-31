from flask import Flask, request, abort, g, render_template, redirect, url_for, send_from_directory, session, flash, current_app
from flask.signals import Namespace
from datetime import datetime
import redis
import time
import ImageFile, Image
import os
import ConfigParser
import cPickle as cP
import bcrypt
import functools
import hashlib

app = Flask(__name__)

app.debug = True
app.secret_key = "A Secret Key" #CHANGE THIS!!!

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'gif', 'jpeg'])

def check_redis():
	"Check to see if we can connect to redis"
	r_server = redis.Redis(db="2channel")
	try:
		r_server.ping()
	except redis.ConnectionError, e:
		print "## ERROR: The redis server appears not to be running."
		raise e
	r_server = None #add the redis stuff to the garbage

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
	
def get_post_opts(subject_line, author_line):
	
	meta = {
		"subject_line": subject_line,
		"author_line": author_line
	}
	
	sl = subject_line.rsplit(get_opt("site", "command_sep", "#!"), 1)
	meta["subject"] = sl[0]
	if len(sl) > 1: meta["command"] = Commands.mapped_method(sl[1])
	
	al = author_line.rsplit("#", 1)
	meta["author"] = al[0]
	if len(al) > 1: meta["trip"] = Tripcode(meta["author"], al[1])
	
	return meta

def require(*rargs):
	"A Decorator to allow a command to require certain meta information..."
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			for a in rargs:
				if a not in kwargs: return redirect(request.environ["HTTP_REFERER"])
			return func(*args, **kwargs)
		return wrapper
	return decorator

class Signals(object):
	_signals = Namespace()
	new_post = _signals.signal("post")

class Tripcode(object):
	
	@classmethod
	def get(self, username):
		return cP.loads(g.r.get("trip:{0}".format(username)))
		
	def __new__(cls, username, passw="", **kwargs):
		"Return the Tripcode instance from redis if the username is already registered"
		if not kwargs.get("skip_check") and g.r.exists("trip:{0}".format(username)):
			return Tripcode.get(username)
		else:
			return super(Tripcode, cls).__new__(cls, username, passw)
	
	def __init__(self, username, trip="", **kwargs):
		if not hasattr(self, "passwd"):
			self.passwd = bcrypt.hashpw(trip, bcrypt.gensalt(5))
			self.username = username
		
	def get_level(self):
		return self.__dict__.get("level")
		
	def set_permission(self, permission_level):
		self.level = permission_level
		
	def set_pass(self, password):
		self.passwd = bcrypt.hashpw(password, bcrypt.gensalt())
		
	def save(self):
		g.r.set("trip:{0}".format(self.username), cP.dumps(self))

class Commands(object):
	
	@classmethod
	def mapped_method(cls, method_name):
		if hasattr(cls, method_name):
			return getattr(cls, method_name)
	
	@classmethod
	@require("trip", "author_line")
	def login(cls, trip=None, author_line="", **kwargs):
		if trip.get_level() in ["admin", "mod"] and \
		bcrypt.hashpw(author_line.rsplit("#", 1)[1], trip.passwd) == trip.passwd:
			print "Password Taken"
			session["level"] = trip.get_level()
			session["user"] = trip.username
		return redirect(request.environ["HTTP_REFERER"])
		
	@classmethod
	def logout(cls, **kwargs):
		if session.get("level"):
			map(session.pop, ("level", "user"))
		return redirect(request.environ["HTTP_REFERER"])
		
	@classmethod
	@require("trip")
	def regi(cls, trip=None, level="mod", **kwargs):
		if session.get("level") == "admin":
			trip.set_permission(level)
			trip.save()
		return redirect(request.environ["HTTP_REFERER"])
		
	@classmethod
	@require("trip", "author_line")
	def cpass(cls, trip=None, author_line="", **kwargs):
		if (session.get("level") == "mod" and session.get("user") == trip.username) or\
		session.get("level") == "admin":
			trip.set_pass(author_line.rsplit("#", 1)[1])
			trip.save()
		return redirect(request.environ["HTTP_REFERER"])
		
	@classmethod
	@require("post")
	def asa(cls, post=None, **kwargs):
		if session.get("level"):
			post.capcode = "## {0} ##".format(session.get("level").capitalize())
			
	@classmethod
	@require("post")
	def sage(cls, post=None, **kwargs):
		if post.is_reply: g.env["sage"] = True
		
	@classmethod
	@require("post")
	def bump(cls, post=None, **kwargs):
		if post.is_reply:
			Thread.bump_thread(post.board, post.thread)
		return redirect(request.environ["HTTP_REFERER"])
		
class PostImage(object):
	
	@classmethod
	def hash(cls, image_stream):
		h = hashlib.sha1()
		image_stream.stream.seek(0, 0) #seek to the begining of the file
		while True: #read the file
			b = image_stream.stream.read(8192)
			if not b: break
			h.update(b)
		return h.hexdigest()
	
	def __new__(cls, image=None):
		if image:
			hash = PostImage.hash(image)
			if g.r.exists("image:{0}".format(hash)):
				instance = cP.loads(g.r.get("image:{0}".format(hash)))
				setattr(instance, "exists", True) ##If loading from pickle, set the exists instance attr
				return instance
			else:
				#Call the parents __new__ constructor to save the image
				return super(PostImage, cls).__new__(cls, image)
				
		#This basically means it's getting unpickled
		return super(PostImage, cls).__new__(cls, image, True)
		
	def __init__(self, image):
		if not hasattr(self, "exists"):
			self.hash = PostImage.hash(image)
			self.__stream  = image.stream
			self.filename = image.filename
			self.id = g.r.incr("u:imageID")
		
	def save(self, thumbnail_size=(250, 250)):
		"Saves an image if the image does not already exist..."
		if not hasattr(self, "exists"): self.__save_routine(thumbnail_size)
		
	def __save_path(self):
		"Returns the path to save the images to"
		return g.conf.get("site", "image_store")
		
	def __save_redis(self):
		if hasattr(self, "_PostImage__stream"): delattr(self, "_PostImage__stream")
		if hasattr(self, "exists"): delattr(self, "exists")
		g.r.set("image:{0}".format(self.hash), cP.dumps(self))
		
	def __save_routine(self, thumbnail_size=(250, 250)):
		extension = self.filename.rsplit('.', 1)[1]
		if '.' in self.filename and extension in ALLOWED_EXTENSIONS:
			
			self.__stream.seek(0, 0) #seek to the begining
			
			#Read the image stream into a PIL Image class
			image_p = ImageFile.Parser()
			image_p.feed(self.__stream.read(-1))
			im = image_p.close()
			
			#save the image
			im.save(os.path.join(self.__save_path(), str(self.id)+"."+extension))
			
			self.resolution = im.size
			self.format = im.format
			
			#thumbnail the image
			im.thumbnail(thumbnail_size, Image.ANTIALIAS)
			im.save(os.path.join(self.__save_path(), ".".join(["thumb", str(self.id), extension])))
			self.__stream.seek(0,2)
			
			self.filesize = self.__stream.tell()
			self.url = str(self.id)+"."+extension
			self.thumb_url = ".".join(["thumb", str(self.id), extension])
			
			self.__save_redis()
	
class Post(object):
	
	@property
	def is_reply(self):
		if hasattr(self, "thread"):
			return True
		return False
		
	def __init__(self, **kwargs):
		self.id = g.r.incr("u:id")
		self.created = datetime.utcnow()
		self.__dict__.update(kwargs)
	
class Board(object):
	
	def __init__(self, board):
		self.short = board
		self.title = g.conf.get("boards", self.short)
		
	def __len__(self):
		return g.r.zcard("board:{0}:threads".format(self.short))
	
	def threads(self, start_index=0, stop_index=-1):
		print "sit", type(start_index), start_index
		print "stt", type(stop_index), stop_index
		return Thread.threads_on_board(self.short, start_index, stop_index)
		
	def prune(self, to_thread_count=250):
		if g.r.zcard("board:{0}:threads".format(self.short)) < to_thread_count:
			return None
		for thread in self.threads(to_thread_count, -1): thread.delete()

class Thread(Post):
	"This is a thread"
	
	def __len__(self):
		"Find the length (number of replies) of a thread"
		return g.r.zcard("thread:{0}:replies".format(self.id))
	
	@classmethod
	def from_id(cls, thread_id):
		return cP.loads(g.r.get("thread:{0}".format(thread_id)))
	
	@classmethod
	def threads_on_board(cls, board, start_index=0, stop_index=-1):
		return [cP.loads(g.r.get("thread:{0}".format(post_id))) for post_id in g.r.zrevrange("board:{0}:threads".format(board), start_index, stop_index) ]
		
	@classmethod
	def bump_thread(cls, board, thread_id):
		g.r.zadd("board:{0}:threads".format(board), thread_id, int(time.time())) #These are swapped in the py-redis api and not to spec
		
	def replies(self, start_index=0, stop_index=-1):
		return Reply.replies_to_thread(self.id, start_index, stop_index)
		
	def delete(self):
		replies = self.replies()
		pipe = g.r.pipeline()
		for reply in replies: reply.delete(pipe=pipe)
		if replies: pipe.delete("thread:{0}:replies".format(self.id))
		pipe.delete("thread:{0}".format(self.id))
		pipe.zrem("board:{0}:threads".format(self.board), self.id)
		pipe.execute()
		
	def save(self):
		g.r.zadd("board:{0}:threads".format(self.board), self.id, self.id) #These are swapped in the py-redis api and not to spec
		g.r.set("thread:{0}".format(self.id), cP.dumps(self, protocol=-1))
		
class Reply(Post):
	"This is a reply"
	
	@classmethod
	def from_id(cls, reply_id):
		return cP.loads(g.r.get("reply:{0}".format(reply_id)))
		
	@classmethod
	def replies_to_thread(cls, thread_id, start_index=0, stop_index=-1):
		return [cP.loads(g.r.get("reply:{0}".format(reply_id))) for reply_id in g.r.zrange("thread:{0}:replies".format(thread_id), start_index, stop_index) ]
		
	def __init__(self, thread_id, **kwargs):
		self.thread = thread_id
		Post.__init__(self, **kwargs)
		
	def delete(self, pipe=None):
		if pipe:
			pipe.delete("reply:{0}".format(self.id))
			pipe.zrem("thread:{0}:replies".format(self.thread), self.id)
		else:
			g.r.pipeline().delete("reply:{0}".format(self.id)).zrem("thread:{0}:replies".format(self.thread), self.id).execute()
			
	def save(self, bump_thread=True):
		g.r.zadd("thread:{0}:replies".format(self.thread), self.id, self.id)
		g.r.set("reply:{0}".format(self.id), cP.dumps(self, protocol=-1))
		if bump_thread and not g.env.get("sage"): Thread.bump_thread(self.board, self.thread)
		
@app.before_request
def setup_globals():
	"Setup the global options."
	g.r = redis.Redis(db="2channel") #Ini Redis
	g.conf = ConfigParser.SafeConfigParser() #Ini the configs
	g.conf.readfp(open("channel.ini"))
	g.env = {}
	
@Signals.new_post.connect_via(app)
def check_valid(sender, meta):
	sec = "{0}:options".format(meta["post"].board)
	
	require_subject = get_opt(sec, "require_reply_subject", False, "bool") if meta["post"].is_reply else get_opt(sec, "require_thread_subject", False, "bool")
	require_author = get_opt(sec, "require_reply_author", False, "bool") if meta["post"].is_reply else get_opt(sec, "require_thread_author", False, "bool")
	
	if require_subject and not meta["post"].subject:
		flash("Reply subject required.")
		abort(400)
	
	if require_author and not meta["post"].author:
		flash("Reply author name required.")
		abort(400);
		
	if meta["post"].is_reply and get_opt(sec, "enable_reply_limit", False, "bool") and \
	len(Thread.from_id(meta["post"].thread)) >= get_opt(sec, "reply_limit", 1000, "int"):
		flash("Reply limit reached...")
		abort(400)
		
@Signals.new_post.connect_via(app)
def check_image(sender, meta):
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
		
	meta["post"].save()
	
@app.route('/')
def index():
	"Index of the site."
	return render_template("index.html")
	
@app.errorhandler(400)
def error(error):
	"Show general error messages sent via flash()s"
	return render_template("error.html", rd=request.base_url)
	
@app.route("/images/<image_hash>/delete")
def delete_image(image_hash):
	"Removes an image"
	
	if session.get("level"):
		if g.r.get("image:{0}".format(image_hash)):
			image_url = cP.loads(g.r.get("image:{0}".format(image_hash))).url
			g.r.delete("image:{0}".format(image_hash))
			try:
				os.remove(os.path.join(g.conf.get("site", "image_store"), image_url))
				os.remove(os.path.join(g.conf.get("site", "image_store"), "thumb."+image_url))
			except OSError:
				flash("No image: {0}".format(image_url))
				abort(400)
		
	return redirect(request.environ.get("HTTP_REFERER", url_for("index")))
		
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
	
@app.route('/images/<filename>')
def uploaded_file(filename):
	"Return an uploaded file."
	return send_from_directory(g.conf.get("site", "image_store"), filename)

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
	if meta.get("command"):
		r = meta["command"](**meta)
		if r: return r
		
	Signals.new_post.send(current_app._get_current_object(), meta=meta)
		
	meta["post"].save()
	
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
		
	if meta.get("command"):
		r = meta["command"](**meta)
		if r: return r
		
	Signals.new_post.send(current_app._get_current_object(), meta=meta) # Send out the new_post signal
	
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
	
if __name__ == '__main__':
	"Run via flask runtime if not running as WSGI"
	import sys
	port = 80 if len(sys.argv) < 2 else int(sys.argv[1])
	app.run(port = port)
	
elif __name__ != '__main__':
	application  = app #so as to comply with wsgi standards
