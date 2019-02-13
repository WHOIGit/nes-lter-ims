from . import logger

from neslter.parsing.files import Resolver
from neslter.parsing.ctd import Ctd
from neslter.parsing.utils import write_dt

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