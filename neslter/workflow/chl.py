# import os
from .api import Workflow

from neslter.parsing.files import Resolver
from neslter.parsing.chl import parse_chl, subset_chl

CHL='chl'

class ChlWorkflow(Workflow):
    def __init__(self, cruise):
        self.cruise = cruise.lower()
    def directories(self):
        return Resolver().directories(CHL, self.cruise, skip_raw=True)
    def filename(self):
        return '{}_chl'.format(self.cruise)
    def produce_product(self):
        chl_path = Resolver().raw_file(CHL, 'NESLTERchl.xlsx')
        parsed = parse_chl(chl_path)
        subset = subset_chl(parsed)
        return subset[subset['cruise'] == self.cruise.upper()]