import shlex
import re

class RegexMatchers(object):
	section = re.compile("<(?P<catagory>.*?)( (?P<options>.*?))?>")
	
class Catagory(object):
	"A Basic object for containg a catagory"
	
	def __init__(self, catagory, options=None, parent=None):
		self._catagory = catagory
		self._options = options
		self._parent = parent
		self._subcatagories = []
		
	def push_catagory(self, catagory):
		self._subcatagories.append(catagory)
		
	def subcatagories(self):
		return self._subcatagories
		
	def catagory(self):
		return self._catagory.lower()
	
	def options(self):
		return self._options
	
	def __setattr__(self, name, value):
		if hasattr(self, name) and not isinstance(getattr(self, name), list):
			l = [getattr(self, name)]
			l.append(value)
			self.__dict__[name] = l
		elif hasattr(self, name) and isinstance(getattr(self, name), list):
			self.__dict__[name].append(value)
		else:
			self.__dict__[name] = value

class ApacheConfig(object):
	"Basic Class For parsing Apache Style Configuration Files"
	def __init__(self, config_file_or_name):
		self.setup_globals(config_file_or_name)
		self.structure = self.parse_file()
		
	def setup_globals(self, config_file_or_name):
		"""
		Pull the initialization out to another function so the __init__ method
		can be safely subclassed.
		"""
		if isinstance(config_file_or_name, file): stream = config_file_or_name
		else: stream = open(config_file_or_name)
		self._shlex = shlex.shlex(instream=stream, posix=True)
		self._shlex.whitespace = "\n"
		self._shlex.whitespace_split = True
		self._shlex.eof = None
		
		self.regexs = RegexMatchers()
		
	def _parse_string(self, st, extra_formatters=[]):
		"Logically parse an item to a specific type"
		
		def boolean(s):
			if s.lower() in ["true", "yes", "on"]: return True
			elif s.lower() in ["false", "no", "off"]: return False
			else:
				raise Exception("Type cannot be coerced into boolean")
		
		formats = [
			lambda x: int(x), #integer
			lambda x: float(x), #float
			lambda x: boolean(x),  #Boolean
		]
		formats.extend(extra_formatters)
		formats.append(lambda x: str(x)) #Add string which should always match
		
		#check the formatter against different parsers
		for fmt in formats:
			try: return fmt(st)
			except: pass
		
	def next_line(self, typed=False, formatters=[]):
		token = self._shlex.get_token()
		if token == None: return token
		line = shlex.split(token)
		if typed:
			for arg in line[1:]:
				line[line.index(arg)] \
				= self._parse_string(arg, extra_formatters=formatters)
		return line, token
		
	def has_line(self):
		t = self._shlex.get_token()
		if t:
			self._shlex.push_token(t)
			return True
		return False
	
	def parse_file(self, catagory_type=Catagory):
		#The main containing catagory
		top = catagory_type("Main")
		
		#The current Catagory
		catagory = top
		
		line, orig = self.next_line()
		while line != None:
			
			match = self.regexs.section.search(" ".join(line))
			if match:
				
				d = match.groupdict()
				if d["catagory"][0] != "/":
					current = catagory_type(d["catagory"],
											options=d["options"],
											parent=catagory)
					catagory.push_catagory(current)
					catagory = current
				elif d["catagory"][0] == "/":
					catagory = catagory._parent
				else: pass
			elif line:
				self._shlex.push_token(orig)
				line, orig = self.next_line(typed=True)
				if len(line) > 2: setattr(catagory, line[0], line[1:])
				else: setattr(catagory, line[0], line[1])
				
			try: line, orig = self.next_line()
			except TypeError: line = None
		return top

if __name__ == '__main__':
	from pprint import pformat
	import copy
	def print_catagory(c, indent=0):
		
		print "{0}{1:#^50}".format("\t"*indent, "Catagory")
		print "{0}Type:".format("\t"*indent), c.catagory()
		print "{0}Options:".format("\t"*indent), c.options()
		print "{0}{1:*^30}".format("\t"*indent, "Values")
		d = copy.deepcopy(c.__dict__)
		map(d.pop, [x for x in d.iterkeys() if x[0] == "_"])
		pf = pformat(d)
		print "\t"*indent, pf.replace("\n", "\n{0}".format("\t"*indent))
		if c.subcatagories():
			print "{0}{1:*^30}".format("\t"*indent, "SubCatagories")
			for i in c.subcatagories():
				print_catagory(i, indent=indent+1)
	
	c = ApacheConfig("pychannel.conf")
	print_catagory(c.structure)
	
	
	
	