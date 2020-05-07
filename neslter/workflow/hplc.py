from .api import Workflow

from neslter.parsing.files import Resolver
from neslter.parsing.hplc import parse_hplc

from .stations import add_nearest_station

HPLC='hplc'

class HplcWorkflow(Workflow):
    def __init__(self, cruise):
        self.cruise = cruise.lower()
    def directories(self):
        return Resolver().directories(HPLC, self.cruise, skip_raw=True)
    def filename(self):
        return '{}_hplc'.format(self.cruise)
    def produce_product(self):
        hplc_dir = Resolver().raw_directory(HPLC)
        all_hplc = parse_hplc(hplc_dir)
        cruise_hplc = all_hplc[all_hplc['cruise'].str.lower() == self.cruise]
        return add_nearest_station(self.cruise, cruise_hplc)