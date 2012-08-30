import os
import sys

def load_plugins(echo=False):
    plugins = {}
    #import the plugins into the `plugins` dict
    channel_path = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(channel_path):
        for file_name in os.listdir(channel_path):
            fname, ext = file_name.rsplit('.', 1)
            if ext == "py" and fname != "__init__":
                if echo: print "Adding plug-in:", fname
                mname = ".".join(["PyChannel", "plugins", fname])
                __import__(mname)
                plugins[fname] = sys.modules[mname]
    return plugins

