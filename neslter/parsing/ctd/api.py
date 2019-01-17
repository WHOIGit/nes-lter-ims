from ..files import Resolver
from .btl import compile_btl_files, summarize_compiled_btl_files
from .hdr import compile_hdr_files
from .asc import parse_cast

class Ctd(object):
    def __init__(self, cruise):
        self.cruise = cruise
        self.dir = Resolver().raw_directory('ctd', cruise)
    def casts(self):
        # return a list of the cast numbers
        return sorted(self.metadata()['cast'].unique())
    def cast(self, cast_number):
        # return data for a specific cast
        return parse_cast(self.dir, cast_number)
    def bottles(self, **kw):
        # return data for each bottle
        return compile_btl_files(self.dir, **kw)
    def bottle_summary(self, **kw):
        # summarize bottle data
        return summarize_compiled_btl_files(self.bottles())
    def metadata(self):
        # return basic metadata from the header files
        return compile_hdr_files(self.dir)