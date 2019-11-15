# import os
from .api import Workflow

from neslter.parsing.files import Resolver
from neslter.parsing.chl import parse_chl, subset_chl, merge_bottle_summary

from neslter.workflow.ctd import CtdBottleSummaryWorkflow

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
        chl = subset[subset['cruise'] == self.cruise.upper()]
        bottle_summary = CtdBottleSummaryWorkflow(self.cruise).produce_product()
        return merge_bottle_summary(chl, bottle_summary)