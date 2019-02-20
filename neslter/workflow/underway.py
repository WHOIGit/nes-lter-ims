from . import logger

from neslter.parsing.files import Resolver
from neslter.parsing.underway import Underway

from .api import Workflow

UNDERWAY = 'underway'

class UnderwayWorkflow(Workflow):
    def __init__(self, cruise):
        self.cruise = cruise
    def directories(self):
        return Resolver().directories(UNDERWAY, self.cruise)
    def filename(self):
        return '{}_underway'.format(self.cruise)
    def produce_product(self):
        return Underway(self.cruise).to_dataframe()