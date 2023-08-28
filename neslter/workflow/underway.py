from . import logger

import pandas as pd

from neslter.parsing.files import Resolver
from neslter.parsing.underway import Underway, DATETIME

from .api import Workflow

UNDERWAY = 'underway'

class UnderwayWorkflow(Workflow):
    def __init__(self, cruise):
        self.cruise = cruise.lower()
    def directories(self):
        return Resolver().directories(UNDERWAY, self.cruise)
    def filename(self):
        return '{}_underway'.format(self.cruise)
    def produce_product(self):
        return Underway(self.cruise).to_dataframe()

class TimeToLocation(object):
    def __init__(self, underway_data):
        """underway data is the product of the underway workflow"""
        self.uw = underway_data.copy()
        self.uw.index = pd.to_datetime(self.uw[DATETIME], utc=True)
    def _infer_lat_lon_cols(self):
        if 'gps_furuno_latitude' in self.uw.columns:
            # FIXME search for other gps models
            return 'gps_furuno_latitude', 'gps_furuno_longitude'
        elif 'dec_lat' in self.uw.columns:
            return 'dec_lat', 'dec_lon'
        else:
            raise KeyError('cannot infer lat/lon columns of underway data')
    def time_to_location(self, time):
        lat_col, lon_col = self._infer_lat_lon_cols()
        index = max(0, self.uw.index.searchsorted(pd.to_datetime(time), utc=True) - 1)
        row = self.uw.iloc[index]
        return row[lat_col], row[lon_col]
    def time_to_lat(self, time):
        return self.time_to_location(time)[0]
    def time_to_lon(self, time):
        return self.time_to_location(time)[1]