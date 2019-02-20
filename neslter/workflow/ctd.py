from . import logger

from .api import Workflow
from neslter.parsing.files import Resolver
from neslter.parsing.ctd import Ctd

CTD = 'ctd'

class CtdWorkflow(Workflow):
    def directories(self):
        return Resolver().directories(CTD, self.cruise)

class CtdCastWorkflow(CtdWorkflow):
    def __init__(self, cruise, cast):
        self.cruise = cruise
        self.cast = cast
    def filename(self):
        return '{}_ctd_cast_{}'.format(self.cruise, self.cast)
    def produce_product(self):
        return Ctd(self.cruise).cast(self.cast)

class CtdBottlesWorkflow(CtdWorkflow):
    def __init__(self, cruise):
        self.cruise = cruise
    def filename(self):
        return '{}_ctd_bottles'.format(self.cruise)
    def produce_product(self):
        return Ctd(self.cruise).bottles()

class CtdBottleSummaryWorkflow(CtdWorkflow):
    def __init__(self, cruise):
        self.cruise = cruise
    def filename(self):
        return '{}_ctd_bottle_summary'.format(self.cruise)
    def produce_product(self):
        return Ctd(self.cruise).bottle_summary()

class CtdMetadataWorkflow(CtdWorkflow):
    def __init__(self, cruise):
        self.cruise = cruise
    def filename(self):
        return '{}_ctd_metadata'.format(self.cruise)
    def produce_product(self):
        return Ctd(self.cruise).metadata()
