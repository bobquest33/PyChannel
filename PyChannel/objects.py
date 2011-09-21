from flask import g, current_app, request, session, redirect
from flask.signals import Namespace
import cPickle as cP
import time
from datetime import datetime
import hashlib
import ImageFile, Image
import os
import bcrypt
import hashlib
import base64

class Signals(object):
	
	def __init__(self):
		self._signals = Namespace()
		
		#General Commands
		self.execute_commands = self._signals.signal("execute_commands")
		
		#Post Signals
		self.new_post = self._signals.signal("post-new")
		self.save_post = self._signals.signal("post-save")
		self.delete_post = self._signals.signal("post-delete")
		
		#Thread Signals
		self.prune_thread = self._signals.signal("prune")
		
		#Image Signals
		self.new_image = self._signals.signal("image-new")
		self.delete_image = self._signals.signal("image-delete")
		
		#Ban Signals
		self.new_ban = self._signals.signal("ban-new")

class Tripcode(object):
	"""An instance of this class is created every time a post is made
	wether or not the poster actually uses a tripcode.
	
	.. note::
	
	   When an instance of this class is created, it checks to see if the user
	   already exists in redis, and if so will authenticate it. If the authtication
	   fails it will just return a normal tripcode. This way if someone tries to make
	   a post using the same name as a mod, it will just generate them a hash like
	   everyone else.
	"""
	BCRYPT_LOG_ROUNDS = 5
	"""Number of log rounds used when hashing the password.
	
	.. note::
	   The higher the number of log rounds the stronger the encryption
	   and the longer ammount of time to generate. The lower the number
	   the weaker the hash and the lower ammount od time to generate
	   a hash."""
	
	@classmethod
	def get(self, username):
		"""Fetches a user from redis if the user exists.
		
		:rtype: :class:`~PyChannel.objects.Tripcode`"""
		if g.r.exists("trip:{0}".format(username)):
			return cP.loads(g.r.get("trip:{0}".format(username)))
		
	def __new__(cls, username="", password=""):
		"Return the Tripcode instance from redis if the username is already registered"
		if g.r.exists("trip:{0}".format(username)) and password and not session.get("level"):
			trip = Tripcode.get(username)
			if trip.permission and trip.check_password(password):
				return trip
			else:
				return super(Tripcode, cls).__new__(cls, username, password)
		elif g.r.exists("trip:{0}".format(username)) and session.get("user") == username:
			return Tripcode.get(username)
		elif username:
			return super(Tripcode, cls).__new__(cls, username, password)
		else:
			return super(Tripcode, cls).__new__(cls)
	
	def __init__(self, username, password):
		self.username = username
		if password: self.pass_hash = base64.b64encode(base64.b16decode(hashlib.md5(password).hexdigest().upper()))[:-2]
		
	@property
	def hash(self):
		"Hash value for a tripcode if one exists"
		if self.password: return None
		else: return self.__dict__.get("pass_hash")
		
	@property
	def permission(self):
		"permission level of this tripcode"
		return self.__dict__.get("level")
		
	@permission.setter
	def permission(self, permission_level):
		"set the permission level of this tripcode"
		self.level = permission_level
		
	@property
	def password(self):
		"password of this tripcode (bcrypt hash)"
		return self.__dict__.get("passwd")
		
	@password.setter
	def password(self, password):
		"set the password of this tripcode, automatically encrypted with bcrypt"
		self.passwd = bcrypt.hashpw(password, bcrypt.gensalt(self.BCRYPT_LOG_ROUNDS))
		
	def check_password(self, password_string):
		"Returns true if the password_string matches the saved password."
		if not self.password: return False #Return if there is no password
		return bcrypt.hashpw(password_string, self.password) == self.password
		
	def save(self):
		"Save the tripcode to redis."
		g.r.set("trip:{0}".format(self.username), cP.dumps(self))
		
class PostImage(object):
	"""A representation of an image for a post."""
	
	@classmethod
	def get_from_hash(cls, hash):
		"""Fetch a previously created image class from redis.
		
		:param hash: A sha1 hash of an image (usually generated with :meth:`~PyChannel.objects.PostImage.hash`)
		:rtype: :class:`~PyChannel.objects.PostImage`"""
		return cP.loads(g.r.get("image:{0}".format(hash)))
	
	@classmethod
	def hash(cls, image_stream):
		"""Get the sha1 hash of an image.
		
		:param image_stream: :class:`StringIO.StringIO`"""
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
		self.ALLOWED_EXTENSIONS = set(['png', 'jpg', 'gif', 'jpeg'])
		if not hasattr(self, "exists"):
			self.hash = PostImage.hash(image)
			self.__stream  = image.stream
			self.filename = image.filename
			self.id = g.r.incr("u:imageID")
		
	def save(self, thumbnail_size=(250, 250)):
		"""Save the image to redis if it does not already exist.
		
		Emmits the :attr:`~PyChannel.objects.Signals.new_image` signal.
		
		:type thumbnail_size: two item tuple (length, width) in pixels"""
		if not hasattr(self, "exists"): self.__save_routine(thumbnail_size)
		g.signals.new_image.send(current_app._get_current_object(), image=self)
		
	def __save_path(self):
		"Fetch the save path from the config file."
		return g.conf.get("site", "image_store")
		
	def __save_redis(self):
		"Remove the unpickleable attributes of the class an save to redis."
		if hasattr(self, "_PostImage__stream"): delattr(self, "_PostImage__stream")
		if hasattr(self, "exists"): delattr(self, "exists")
		g.r.set("image:{0}".format(self.hash), cP.dumps(self))
		
	def __save_routine(self, thumbnail_size=(250, 250)):
		"Thumbnail the image and save it to disk if it has an allowed extension."
		extension = self.filename.rsplit('.', 1)[1].lower()
		if '.' in self.filename and extension in self.ALLOWED_EXTENSIONS:
			
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
		else:
			if hasattr(self, "_PostImage__stream"): delattr(self, "_PostImage__stream")
			if hasattr(self, "exists"): delattr(self, "exists")
	
class Post(object):
	"""A generic post. Inherited by both :class:`~PyChannel.objects.Thread` and :class:`~PyChannel.objects.Reply`."""
	
	@property
	def is_reply(self):
		"Returns True if this instance is a reply."
		if hasattr(self, "thread"):
			return True
		return False
		
	def __init__(self, **kwargs):
		self.id = g.r.incr("u:id")
		self.created_by = request.remote_addr
		self.created = datetime.utcnow()
		self.__dict__.update(kwargs)
	
class Board(object):
	"""An imageboard.
	
	:param board: The short code of the board ie. 'g' for /g/"""
	
	def __init__(self, board):
		self.short = board
		self.title = g.conf.get("boards", self.short)
		
	def __len__(self):
		"The number of threads on this board."
		return g.r.zcard("board:{0}:threads".format(self.short))
	
	def threads(self, start_index=0, stop_index=-1):
		"""Return the threads on this board from *start_index* to *stop_index*.
		
		calls :meth:`PyChannel.objects.Thread.threads_on_board`."""
		return Thread.threads_on_board(self.short, start_index, stop_index)
		
	def prune(self, to_thread_count=250):
		":term:`Prune <Pruning>` the board to to_thread_count."
		if g.r.zcard("board:{0}:threads".format(self.short)) < to_thread_count:
			return None
		for thread in self.threads(to_thread_count, -1):
			g.signals.prune_thread.send(current_app._get_current_object(), thread=thread)
			thread.delete()

class Thread(Post):
	
	def __len__(self):
		"Find the length (number of replies) of a thread"
		return g.r.zcard("thread:{0}:replies".format(self.id))
	
	@classmethod
	def from_id(cls, thread_id):
		"""Fetch the thread with *thread_id* from redis.
		
		:rtype: :class:`~PyChannel.objects.Thread`"""
		return cP.loads(g.r.get("thread:{0}".format(thread_id)))
	
	@classmethod
	def threads_on_board(cls, board, start_index=0, stop_index=-1):
		"Fetch the threads on *board* from *start_index* to *stop_index*"
		return [Thread.from_id(post_id) for post_id in g.r.zrevrange("board:{0}:threads".format(board), start_index, stop_index) ]
		
	@classmethod
	def bump_thread(cls, board, thread_id):
		"Bump thread with id *thread_id* on *board*."
		thread = Thread.from_id(thread_id)
		if thread.sticky: pass
		else: g.r.zadd("board:{0}:threads".format(board), thread_id, int(time.time())) #These are swapped in the py-redis api and not to spec
		
	@property
	def sticky(self):
		"Returns True if the thread is sticky."
		if hasattr(self, "_sticky"):
			return self._sticky
		else:
			return False
		
	@sticky.setter
	def sticky(self, value):
		if value: self._sticky = True
		else: self._sticky = False
		
	def replies(self, start_index=0, stop_index=-1):
		"""Fetches replies to the current thread from redis.
		
		calls :meth:`~PyChannel.objects.Reply.replies_to_thread`"""
		return Reply.replies_to_thread(self.id, start_index, stop_index)
		
	def delete(self):
		"Delete the current thread and all of it's replies."
		replies = self.replies()
		pipe = g.r.pipeline()
		for reply in replies: reply.delete(pipe=pipe)
		if replies: pipe.delete("thread:{0}:replies".format(self.id))
		pipe.delete("thread:{0}".format(self.id))
		pipe.zrem("board:{0}:threads".format(self.board), self.id)
		pipe.execute()
		
	def save(self, score=None):
		"Save the thread with *score*. If score is None then :func:`time.time` will be used."
		if not score: score = int(time.time())
		g.r.zadd("board:{0}:threads".format(self.board), self.id, score) #These are swapped in the py-redis api and not to spec
		g.r.set("thread:{0}".format(self.id), cP.dumps(self, protocol=-1))
		
class Reply(Post):
	"""
	:param thread_id: The id of the owning thread.
	"""
	
	@classmethod
	def from_id(cls, reply_id):
		"""Fetch a reply with id *reply_id* from redis.
		
		:rtype: :class:`~PyChannel.objects.Reply`"""
		return cP.loads(g.r.get("reply:{0}".format(reply_id)))
		
	@classmethod
	def replies_to_thread(cls, thread_id, start_index=0, stop_index=-1):
		"A list of replies to thread with id *thread_id* from *start_index* to *stop_index*."
		return [Reply.from_id(reply_id) for reply_id in g.r.zrange("thread:{0}:replies".format(thread_id), start_index, stop_index) ]
		
	def __init__(self, thread_id, **kwargs):
		self.thread = thread_id
		Post.__init__(self, **kwargs)
		
	def delete(self, pipe=None):
		"Delete the current reply."
		if pipe:
			pipe.delete("reply:{0}".format(self.id))
			pipe.zrem("thread:{0}:replies".format(self.thread), self.id)
		else:
			g.r.pipeline().delete("reply:{0}".format(self.id)).zrem("thread:{0}:replies".format(self.thread), self.id).execute()
			
	def save(self, bump_thread=True):
		"Save the reply to redis and bump the owning thread if *bump_thread* is true."
		g.r.zadd("thread:{0}:replies".format(self.thread), self.id, self.id)
		g.r.set("reply:{0}".format(self.id), cP.dumps(self, protocol=-1))
		if bump_thread and not g.env.get("sage"): Thread.bump_thread(self.board, self.thread)