# import os
from .api import Workflow

from neslter.parsing.files import Resolver
from neslter.parsing.chl import parse_chl, subset_chl, merge_bottle_summary, merge_project_info
from neslter.parsing.samplelog import parse_sample_log

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
        chl = parse_chl(chl_path)
        sample_log_path = Resolver().raw_file(data_type=None, name='LTER_sample_log.xls')
        parsed_sample_log = parse_sample_log(sample_log_path)
        chl = merge_project_info(chl, parsed_sample_log)
        chl = subset_chl(chl)
        chl = chl[chl['cruise'] == self.cruise.upper()]
        bottle_summary = CtdBottleSummaryWorkflow(self.cruise).produce_product()
        return merge_bottle_summary(chl, bottle_summary)