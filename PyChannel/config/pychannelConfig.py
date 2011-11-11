from PyChannel.config.pyconf import ApacheConfig, Catagory
from PyChannel.objects import Board
	
class MergeableCatagory(Catagory):
	
	def merge(self, catagory, force=False):
		"Merge two catagories together"
		for name, value in catagory.__dict__.iteritems():
			if force or not hasattr(self, name):
				setattr(self, name, value)

class PyChannelConfig(ApacheConfig):
	"""
	The config for PyChannel Based in an apache Style
	It mostly contains helper functions...
	"""
	
	def __init__(self, config_file_or_name):
		self.setup_globals(config_file_or_name)
		self.structure = self.parse_file(catagory_type=MergeableCatagory)
		
	def _parse_board(self, b):
		if b.options():
			sp = b.options().split(":", 1)
			return Board(sp[0], ":".join(sp[1:]), catagory=b)
	
	def boards(self):
		return map(self._parse_board, filter(lambda x: x.catagory().lower() == "board",
											 self.structure.subcatagories()))
		
	def board(self, short):
		for board in self.boards():
			if board.short == short: return board
		
	def __getattr__(self, name):
		return getattr(self.structure, name)