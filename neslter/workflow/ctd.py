import pandas as pd

from . import logger

from .api import Workflow
from neslter.parsing.files import Resolver
from neslter.parsing.ctd import Ctd

from .stations import StationsWorkflow

from neslter.parsing.files import DataNotFound
from neslter.workflow.stations import add_nearest_station

CTD = 'ctd'

class CtdWorkflow(Workflow):
    def directories(self):
        return Resolver().directories(CTD, self.cruise)

class CtdCastWorkflow(CtdWorkflow):
    def __init__(self, cruise, cast):
        self.cruise = cruise.lower()
        self.cast = cast
    def filename(self):
        return '{}_ctd_cast_{}'.format(self.cruise, self.cast)
    def produce_product(self):
        cast_data = Ctd(self.cruise).cast(self.cast)
        # now add timestamps
        md = CtdMetadataWorkflow(self.cruise).get_product()
        if not 'times' in cast_data.columns: # no time data available
            return cast_data # this is OK
        # the following will raise IndexError if cast is not in cast metadata
        try:
            cast_start = pd.to_datetime(md[md.cast == str(self.cast)].iloc[0].date)
        except IndexError:
            cast_start = pd.to_datetime(md[md.cast.astype('string').str.lstrip("0") == self.cast.lstrip("0")].iloc[0].date)
        timestamp = cast_start + pd.to_timedelta(cast_data['times'], unit='s')
        cast_data['date'] = timestamp
        return cast_data

class CtdBottlesWorkflow(CtdWorkflow):
    def __init__(self, cruise):
        self.cruise = cruise.lower()
    def filename(self):
        return '{}_ctd_bottles'.format(self.cruise)
    def produce_product(self):
        return Ctd(self.cruise).bottles()

class CtdBottleSummaryWorkflow(CtdWorkflow):
    def __init__(self, cruise):
        self.cruise = cruise.lower()
    def filename(self):
        return '{}_ctd_bottle_summary'.format(self.cruise)
    def produce_product(self):
        return Ctd(self.cruise).bottle_summary()

class CtdMetadataWorkflow(CtdWorkflow):
    def __init__(self, cruise):
        self.cruise = cruise.lower()
    def filename(self):
        return '{}_ctd_metadata'.format(self.cruise)
    def produce_product(self):
        md = Ctd(self.cruise).metadata()
        try:
            return add_nearest_station(self.cruise, md)
        except DataNotFound:
            return md
