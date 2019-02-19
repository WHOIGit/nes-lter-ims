from . import logger

from neslter.parsing.files import Resolver, find_file
from neslter.parsing.utils import write_dt
from neslter.parsing.underway import Underway

UNDERWAY = 'underway'

class UnderwayResolver(Resolver):
    def __init__(self, cruise, **kw):
        super(UnderwayResolver, self).__init__(**kw)
        self.cruise = cruise
    def find_file(self):
        filename = '{}_underway'.format(self.cruise)
        dirs = self.directories(UNDERWAY, self.cruise)
        return filename, find_file(dirs, filename, extension='csv')

def generate_underway_products(cruise, fail_fast=False):
    resolver = Resolver()
    try:
        underway = Underway(cruise) # this parses
        dt = underway.to_dataframe() 
    except:
        logger.warn('underway logs for {} failed to parse'.format(cruise))
        if fail_fast:
            raise
        else:
            return
    filename = dt.metadata['filename']
    pp = resolver.product_file('underway', cruise, filename, makedirs=True)
    write_dt(dt, pp)