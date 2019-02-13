from . import logger

from neslter.parsing.files import Resolver

from .ctd import generate_ctd_products
from .elog import generate_elog_products
from .underway import generate_underway_products

def generate_products(cruise, fail_fast=False):
    logger.info('generating products for {}'.format(cruise))
    logger.info('generating CTD products for {}'.format(cruise))
    generate_ctd_products(cruise, fail_fast=fail_fast)
    logger.info('generating underway products for {}'.format(cruise))
    generate_underway_products(cruise, fail_fast=fail_fast)
    logger.info('generating event log products for {}'.format(cruise))
    generate_elog_products(cruise, fail_fast=fail_fast)
    logger.info('done generating products for {}'.format(cruise))

def generate_all_products(fail_fast=False):
    logger.info('generating products')
    resolver = Resolver()
    for cruise in resolver.cruises():
        generate_products(cruise, fail_fast=fail_fast)
    logger.info('product generation complete')