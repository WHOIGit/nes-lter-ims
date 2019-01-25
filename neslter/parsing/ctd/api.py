from ..files import Resolver, FILENAME
from ..utils import data_table

from .btl import compile_btl_files, summarize_compiled_btl_files
from .hdr import compile_hdr_files
from .asc import parse_cast

class Ctd(object):
    def __init__(self, cruise, raw_directory=None):
        self.cruise = cruise
        if raw_directory is None:
            self.dir = Resolver().raw_directory('ctd', cruise)
        else:
            self.dir = raw_directory
    def casts(self):
        # return a list of the cast numbers
        return [int(i) for i in sorted(self.metadata()['cast'].unique())]
    def cast(self, cast_number):
        # return data for a specific cast
        df = parse_cast(self.dir, cast_number)
        filename = '{}_ctd_cast_{}'.format(self.cruise, cast_number)
        return data_table(df, filename=filename)
    def bottles(self, **kw):
        # return data for each bottle
        df = compile_btl_files(self.dir, **kw)
        filename = '{}_ctd_bottles'.format(self.cruise)
        return data_table(df, filename=filename)
    def bottle_summary(self, **kw):
        # summarize bottle data
        df = self.bottles(summary=True)
        filename = '{}_ctd_bottle_summary'.format(self.cruise)
        return data_table(df, filename=filename)
    def metadata(self):
        # return basic metadata from the header files
        df = compile_hdr_files(self.dir)
        filename = '{}_ctd_metadata'.format(self.cruise)
        return data_table(df, filename=filename)
