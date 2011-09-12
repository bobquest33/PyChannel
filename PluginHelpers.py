#This module is for circular import troubles
from flask import g

class PluginHandler(object):
	
	def __init__(self):
		self.registered_funcs = []
		
	def register(self, signal_name):
		def decorator(func):
			self.registered_funcs.append((signal_name, func))
			return func
		return decorator
	
	def plug_in(self):
		for func in self.registered_funcs:
			if hasattr(g.signals, func[0]):
				getattr(g.signals, func[0]).connect(func[1])
			else:
				raise ValueError("No signal: %s"% func[0])