import logging

logging.basicConfig()

from neslter.parsing.files import Resolver
from neslter.parsing.utils import write_dt
from neslter.parsing.elog import EventLog

def generate_events_product(cruise, fail_fast=False):
    resolver = Resolver()
    elog = EventLog(cruise)
