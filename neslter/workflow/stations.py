from neslter.parsing.stations import Stations, StationLocator
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

def add_nearest_station(cruise, product, require=False):
    st_wf = StationsWorkflow(cruise)
    try:
        smd = st_wf.get_product()
        station_locator = StationLocator(smd)
        return station_locator.cast_to_station(product)
    except KeyError:
        # no station metadata. That's OK
        if require:
            raise
    return product