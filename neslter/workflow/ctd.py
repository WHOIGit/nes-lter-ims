from . import logger

from neslter.parsing.files import Resolver, find_file
import os

from neslter.parsing.ctd import Ctd
from neslter.parsing.utils import write_dt

CTD = 'ctd'

class CtdResolver(Resolver):
    def __init__(self, cruise, **kw):
        super(CtdResolver, self).__init__(**kw)
        self.cruise = cruise
    def find_file(self, filename):
        dirs = self.directories(CTD, self.cruise)
        return filename, find_file(dirs, filename, extension='csv')
    def cast(self, cast_number):
        filename = '{}_ctd_cast_{}'.format(self.cruise, cast_number)
        return self.find_file(filename)
    def bottles(self):
        # return data for each bottle
        filename = '{}_ctd_bottles'.format(self.cruise)
        return self.find_file(filename)
    def bottle_summary(self):
        # summarize bottle data
        filename = '{}_ctd_bottle_summary'.format(self.cruise)
        return self.find_file(filename)
    def metadata(self):
        # return basic metadata from the header files
        filename = '{}_ctd_metadata'.format(self.cruise)
        return self.find_file(filename)

def generate_ctd_products(cruise, fail_fast=False):
    resolver = Resolver()
    try:
        parser = Ctd(cruise)
    except:
        logger.warn('ctd raw files for {} not found'.format(cruise))
        if fail_fast:
            raise
        else:
            return
    def write_product_file(dt):
        if dt is None:
            return
        filename = dt.metadata['filename']
        pp = resolver.product_file('ctd', cruise, filename, makedirs=True)
        try:
            write_dt(dt, pp)
        except:
            if fail_fast:
                raise
            logging.warn('could not write product file {}'.format(pp))
    # generate casts
    dt = None
    for cast_number in parser.casts():
        try:
            dt = parser.cast(cast_number)
        except:
            logging.warn('{} cast {} failed to parse'.format(cruise, cast))
            if fail_fast:
                raise
            continue
        write_product_file(dt)
    # generate compiled bottle files
    dt = None
    try:
        dt = parser.bottles()
    except:
        logging.warn('{} bottles failed to parse'.format(cruise))
        if fail_fast:
            raise
    write_product_file(dt)
    # generate bottle summary file
    dt = None
    try:
        dt = parser.bottle_summary()
    except:
        logging.warn('{} bottle summary failed to parse'.format(cruise))
        if fail_fast:
            raise
    write_product_file(dt)
    # generate ctd metadata file
    dt = None
    try:
        dt = parser.metadata()
    except:
        logging.warn('{} ctd metadata failed to parse'.format(cruise))
        if fail_fast:
            raise
    write_product_file(dt)