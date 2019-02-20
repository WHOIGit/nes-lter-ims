from neslter.parsing.stations import Stations
from .api import Workflow

from neslter.parsing.files import Resolver

METADATA = 'metadata'

class StationsWorkflow(Workflow):
    def __init__(self, cruise):
        self.cruise = cruise
    def directories(self):
        return Resolver().directories(METADATA, self.cruise)
    def filename(self):
        return '{}_stations'.format(self.cruise)
    def produce_product(self):
        return Stations(self.cruise).to_dataframe()
