import shlex
import re

class RegexMatchers():
    section = re.compile("<(?P<catagory>.*?)( (?P<options>.*?))?>")
    
class Catagory(object):
    "A Basic object for containg a catagory"
    
    def __init__(self, catagory, options=None, parent=None, lists=[]):
        self.__dict__["_lists"] = [ x.lower() for x in lists]
        self._catagory = catagory
        self._options = options
        self._parent = parent
        self._subcatagories = []
        
    def push(self, catagory):
        self._subcatagories.append(catagory)
        
    def children(self):
        return self._subcatagories
        
    def catagory(self):
        return self._catagory
    
    def options(self):
        return self._options
    
    def update(self, d):
        for k, v in d.iteritems():
            if isinstance(v, list): self._set_list(k, v)
            else: setattr(self, k, v)
            
    def fill(self, d):
        for k, v in d.iteritems():
            if not hasattr(self, k.lower()):
                if isinstance(v, list): self._set_list(k, v)
                else: setattr(self, k, v)
                
    def _set_list(self, key, list):
        for x in list:
            setattr(self, key, x)
            
    def __getattr__(self, name):
        if not name in self.__dict__:
            if name in self._lists: return []
            else: return None
        return self.__dict__[name]
    
    def __setattr__(self, name, value):
        name = name.lower()
        
        if not self.__dict__.get(name) \
        and name in self._lists \
        and not hasattr(self, name):
            self.__dict__[name] = [value]
            
        elif self.__dict__.get(name) \
        and isinstance(getattr(self, name), list):
            self.__dict__[name].append(value)
            
        else:
            self.__dict__[name] = value

class ApacheConfig(object):
    "Basic Class For parsing Apache Style Configuration Files"
    def __init__(self, config_file_or_name, catagory_class=Catagory):
        self.setup_globals(config_file_or_name)
        self.catagory_class = catagory_class
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
        
    def _type_string(self, st, extra_formatters=[]):
        "Logically parse an item to a specific type"
        
        def boolean(s):
            if s.lower() in ["true", "yes", "on"]: return True
            elif s.lower() in ["false", "no", "off"]: return False
            else:
                raise TypeError("Type cannot be coerced into boolean.")
        
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
                = self._type_string(arg, extra_formatters=formatters)
        return line, token
        
    def has_line(self):
        t = self._shlex.get_token()
        if t:
            self._shlex.push_token(t)
            return True
        return False
    
    def parse_file(self):
        #The main containing catagory
        top = self.catagory_class("Main")
        
        #The current Catagory
        catagory = top
        
        line, orig = self.next_line()
        while line != None:
            
            match = self.regexs.section.search(" ".join(line))
            if match:
                
                d = match.groupdict()
                if d["catagory"][0] != "/": #found a catagory
                    
                    current = self.catagory_class(d["catagory"],
                                       d["options"],
                                       parent=catagory)
                    catagory.push(current)
                    catagory = current
                    
                elif d["catagory"][0] == "/": #found the end of a catagory
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
        if c.children():
            print "{0}{1:*^30}".format("\t"*indent, "SubCatagories")
            for i in c.children():
                print_catagory(i, indent=indent+1)
    
    c = ApacheConfig("pychannel.conf")
    print_catagory(c.structure)
    
# g.conf.board("b") (or just ) .b.Disable
    
    
    
    
