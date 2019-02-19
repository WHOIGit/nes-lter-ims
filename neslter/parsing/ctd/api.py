from ..files import Resolver, FILENAME
from ..utils import data_table

from .btl import compile_btl_files, summarize_compiled_btl_files
from .hdr import compile_hdr_files
from .asc import parse_cast

class Ctd(object):
    def __init__(self, cruise, check_exists=True):
        self.cruise = cruise
        self.raw_dir = Resolver().raw_directory('ctd', cruise)
    def cast(self, cast_number):
        return parse_cast(self.raw_dir, cast_number)
    def bottles(self, **kw):
        # return data for each bottle
        return compile_btl_files(self.raw_dir, **kw)
    def bottle_summary(self, **kw):
        # summarize bottle data
        return self.bottles(summary=True)
    def metadata(self):
        # return basic metadata from the header files
        return compile_hdr_files(self.raw_dir)
