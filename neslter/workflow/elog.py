from . import logger

from neslter.parsing.files import Resolver
from neslter.parsing.elog import EventLog

from .api import Workflow

EVENT_LOG = 'elog'

class EventLogWorkflow(Workflow):
    def __init__(self, cruise):
        self.cruise = cruise.lower()
    def directories(self):
        return Resolver().directories(EVENT_LOG, self.cruise)
    def filename(self):
        return '{}_elog'.format(self.cruise)
    def produce_product(self):
        return EventLog(self.cruise).to_dataframe()