from PyChannel.helpers.plugin import ImmediateRedirect
from PyChannel.helpers.channel import get_opt
import functools

def require(*rargs):
	"A Decorator to allow a command to require certain meta information..."
	def decorator(func):
		@functools.wraps(func)
		def wrapper(sender, meta):
			if not meta.get("command") or not meta["command"] == func.__name__:
				return None
			if meta.get("post") and not get_opt("{0}:commands".format(meta["post"].board), meta["command"], True, "bool"):
				raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
			for a in rargs:
				if a not in meta:
					raise ImmediateRedirect(redirect(request.environ["HTTP_REFERER"]))
			return func(sender, meta)
		return wrapper
	return decorator