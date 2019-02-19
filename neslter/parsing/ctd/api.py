from ..files import Resolver, FILENAME
from ..utils import data_table

from .btl import compile_btl_files, summarize_compiled_btl_files
from .hdr import compile_hdr_files
from .asc import parse_cast

class Ctd(object):
    def __init__(self, cruise, check_exists=True):
        self.cruise = cruise
        self.raw_dir = Resolver().raw_directory('ctd', cruise)
    def casts(self):
        # return a list of the cast numbers
        return [int(i) for i in sorted(self.metadata()['cast'].unique())]
    def cast(self, cast_number):
        filename = '{}_ctd_cast_{}'.format(self.cruise, cast_number)
        # return data for a specific cast
        df = parse_cast(self.raw_dir, cast_number)
        return data_table(df, filename=filename)
    def bottles(self, **kw):
        # return data for each bottle
        filename = '{}_ctd_bottles'.format(self.cruise)
        df = compile_btl_files(self.raw_dir, **kw)
        return data_table(df, filename=filename)
    def bottle_summary(self, **kw):
        # summarize bottle data
        filename = '{}_ctd_bottle_summary'.format(self.cruise)
        df = self.bottles(summary=True)
        return data_table(df, filename=filename)
    def metadata(self):
        # return basic metadata from the header files
        filename = '{}_ctd_metadata'.format(self.cruise)
        df = compile_hdr_files(self.raw_dir)
        return data_table(df, filename=filename)
