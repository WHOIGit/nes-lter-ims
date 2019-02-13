from . import logger

from neslter.parsing.files import Resolver
from neslter.parsing.utils import write_dt
from neslter.parsing.underway import Underway

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