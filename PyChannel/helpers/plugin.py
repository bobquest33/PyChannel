#This module is for circular import troubles
from flask import g

class ImmediateRedirect(Exception):
	"Immediately Redirect a request"
	
	def __init__(self, redirect_object):
		self.r = redirect_object

class PluginHandler(object):
	
	def __init__(self):
		self.registered_funcs = []
		self._plugged = False
		self._registered_signals = []
		
	def register(self, signal_name):
		def decorator(func):
			self.registered_funcs.append((signal_name, func))
			return func
		return decorator
	
	def signal(self, signal_name):
		"Add a scoped signal to this this plug instance"
		self._registered_signals.append(signal_name)
	
	def fire(self, signal_name, **kwargs):
		if not self._plugged: return None
		if hasattr(g.signals, signal_name):
			getattr(g.signals, signal_name).send(self, **kwargs)
		else:
			raise ValueError("No signal: %s"% signal_name)
			
	def plug_signals(self):
		for signal in self._registered_signals:
			if not hasattr(g.signals, signal): setattr(g.signals, signal, g.signals._signals.signal(signal))
	
	def plug_in(self):
		for func in self.registered_funcs:
			if hasattr(g.signals, func[0]):
				getattr(g.signals, func[0]).connect(func[1])
			else:
				raise ValueError("No signal: %s"% func[0])
		self._plugged = True