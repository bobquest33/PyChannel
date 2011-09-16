from flask import g, current_app
import cPickle as cP
import time
from datetime import datetime
import hashlib
import ImageFile, Image
import os
import bcrypt

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
		
class PostImage(object):
	
	@classmethod
	def get_from_hash(cls, hash):
		return cP.loads(g.r.get("image:{0}".format(hash)))
	
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
		self.ALLOWED_EXTENSIONS = set(['png', 'jpg', 'gif', 'jpeg'])
		if not hasattr(self, "exists"):
			self.hash = PostImage.hash(image)
			self.__stream  = image.stream
			self.filename = image.filename
			self.id = g.r.incr("u:imageID")
		
	def save(self, thumbnail_size=(250, 250)):
		"Saves an image if the image does not already exist..."
		if not hasattr(self, "exists"): self.__save_routine(thumbnail_size)
		g.signals.new_image.send(current_app._get_current_object(), image=self)
		
	def __save_path(self):
		"Returns the path to save the images to"
		return g.conf.get("site", "image_store")
		
	def __save_redis(self):
		if hasattr(self, "_PostImage__stream"): delattr(self, "_PostImage__stream")
		if hasattr(self, "exists"): delattr(self, "exists")
		g.r.set("image:{0}".format(self.hash), cP.dumps(self))
		
	def __save_routine(self, thumbnail_size=(250, 250)):
		extension = self.filename.rsplit('.', 1)[1]
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
		return Thread.threads_on_board(self.short, start_index, stop_index)
		
	def prune(self, to_thread_count=250):
		if g.r.zcard("board:{0}:threads".format(self.short)) < to_thread_count:
			return None
		for thread in self.threads(to_thread_count, -1):
			g.signals.prune_thread.send(current_app._get_current_object(), thread=thread)
			thread.delete()

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
		thread = Thread.from_id(thread_id)
		if thread.sticky: pass
		else: g.r.zadd("board:{0}:threads".format(board), thread_id, int(time.time())) #These are swapped in the py-redis api and not to spec
		
	@property
	def sticky(self):
		if hasattr(self, "_sticky"):
			return self._sticky
		else:
			return False
		
	@sticky.setter
	def sticky(self, value):
		if value: self._sticky = True
		else: self._sticky = False
		
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
		
	def save(self, score=None):
		if not score: score = int(time.time())
		g.r.zadd("board:{0}:threads".format(self.board), self.id, score) #These are swapped in the py-redis api and not to spec
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