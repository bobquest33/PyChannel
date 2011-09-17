#This module is for circular import troubles
from flask import g

class PluginHandler(object):
	
	def __init__(self):
		self.registered_funcs = []
		self._plugged = False
		
	def register(self, signal_name):
		def decorator(func):
			self.registered_funcs.append((signal_name, func))
			return func
		return decorator
	
	def fire(self, signal_name, **kwargs):
		if not self._plugged: return None
		if hasattr(g.signals, signal_name):
			getattr(g.signals, signal_name).send(self, **kwargs)
		else:
			raise ValueError("No signal: %s"% signal_name)
	
	def plug_in(self):
		self._plugged = False
		for func in self.registered_funcs:
			if hasattr(g.signals, func[0]):
				getattr(g.signals, func[0]).connect(func[1])
			else:
				raise ValueError("No signal: %s"% func[0])