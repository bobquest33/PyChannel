from PyChannel.config import pyconf
from PyChannel.objects import Board

class Config(pyconf.ApacheConfig):
    """
    The config for PyChannel Based in an apache Style
    It mostly contains helper functions...
    """
    
    def _parse_board(self, b):
        if b.options():
            sp = b.options().split(":", 1)
            return Board(sp[0], ":".join(sp[1:]), catagory=b)
    
    def _find_boards(self):
        return map(self._parse_board, filter(lambda x: x.catagory().lower() == "board",
                                             self.structure.children()))
        
    def _parse_boards(self):
        st = {}
        for b in self._find_boards():
            st[b.short] = b
        return st
    
    def __init__(self, config_file, listers=["require", "disable"]):
        class ListingCatagory(pyconf.Catagory):
            
            def __init__(self, *args, **kwargs):
                kwargs["lists"] = listers
                pyconf.Catagory.__init__(self, *args, **kwargs)
        
        super(Config, self).__init__(config_file,
                                     catagory_class=ListingCatagory)
        self.boards = self._parse_boards()
            
    def __getitem__(self, name):
        return getattr(self, name)
        
    def __setitem__(self, name, value):
        self.__dict__[name] = value
        
    def update(self, d):
        self.__dict__.update(d)
        
    def __contains__(self, item):
        return item in self.__dict__

    def __getattr__(self, name):
        name = name.lower()
        if name in self:
            return self[name]
        else:
            return getattr(self.structure, name)
