from . import logger

from neslter.parsing.files import Resolver, find_file
from neslter.parsing.utils import write_dt
from neslter.parsing.elog import EventLog

EVENT_LOG = 'elog'

class EventLogResolver(Resolver):
    def __init__(self, cruise, **kw):
        super(EventLogResolver, self).__init__(**kw)
        self.cruise = cruise
    def find_file(self):
        filename = '{}_elog'.format(self.cruise)
        dirs = self.directories(EVENT_LOG, self.cruise)
        return filename, find_file(dirs, filename, extension='csv')

def generate_elog_products(cruise, fail_fast=False):
    resolver = Resolver()
    try:
        elog = EventLog(cruise) # this parses
    except:
        logger.warn('event log for {} failed to parse'.format(cruise))
        if fail_fast:
            raise
        else:
            return
    dt = elog.to_dataframe()
    filename = dt.metadata['filename']
    pp = resolver.product_file('elog', cruise, filename, makedirs=True)
    write_dt(dt, pp)