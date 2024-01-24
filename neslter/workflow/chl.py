# import os
import pandas as pd

from .api import Workflow

from neslter.parsing.files import DataNotFound, Resolver
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
        if self.cruise.lower() == 'all':
            chl = subset
            bottle_summaries = []
            for cruise in Resolver().cruises():
                try:
                    bottle_summaries.append(CtdBottleSummaryWorkflow(cruise).produce_product())
                except DataNotFound: # this is OK, some cruises don't have data
                    pass
            if not bottle_summaries:
                raise DataNotFound('no bottle summary data found')
            bottle_summary = pd.concat(bottle_summaries)
        else:
            chl = subset[subset['cruise'] == self.cruise.upper()]
            bottle_summary = CtdBottleSummaryWorkflow(self.cruise).produce_product()
        return merge_bottle_summary(chl, bottle_summary).sort_values('date')