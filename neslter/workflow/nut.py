import os

from .api import Workflow

from neslter.parsing.files import Resolver
from neslter.parsing.nut import merge_nut_bottles

from neslter.workflow.ctd import CtdBottleSummaryWorkflow, CtdBottlesWorkflow

from .stations import add_nearest_station

NUT='nut'

class NutPlusBottlesWorkflow(Workflow):
    def __init__(self, cruise):
        self.cruise = cruise.lower()
    def directories(self):
        return Resolver().directories(NUT, self.cruise, skip_raw=True)
    def filename(self):
        return '{}_nut'.format(self.cruise)
    def produce_product(self):
        bottle_summary = CtdBottleSummaryWorkflow(self.cruise).get_product()
        bottles = CtdBottlesWorkflow(self.cruise).get_product()
        nut_path = Resolver().raw_file(NUT, 'LTERnut.xlsx')
        parent_dir = os.path.dirname(os.path.dirname(nut_path)) # ..
        sample_log_path = os.path.join(parent_dir, 'LTER_sample_log.xlsx')
        merged = merge_nut_bottles(sample_log_path, nut_path, bottle_summary, bottles, self.cruise)
        return add_nearest_station(self.cruise, merged)