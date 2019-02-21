import re
from io import StringIO
import os
from glob import glob
import warnings

import pandas as pd
import numpy as np

from .files import Resolver, cruise_to_vessel, ENDEAVOR, ARMSTRONG
from .utils import data_table

from neslter.parsing.ctd.hdr import HdrFile
from neslter.parsing.utils import clean_column_names, doy_to_datetime, date_time_to_datetime

DATETIME_ISO8601 = 'DateTime_ISO8601'
DATETIME = 'date' # this column name round-trips with df.to_json

ENDEAVOR_GPS_MODEL = 'furuno'

UNDERWAY = 'underway'

class _EndeavorParser(object):
    def __init__(self, csv_dir, resolution=60):
        self.df = self.parse(csv_dir, resolution)
    def parse(self, csv_dir, resolution=60):
        """compile daily underway files"""
        assert resolution in [1, 60] # not aware of any other resolutions
        dfs = []
        for fn in sorted(os.listdir(csv_dir)):
            # files have names like Data60Sec_Daily_20180204-000000.csv
            if not re.match(r'Data{}Sec_Daily_\d+-\d+\.csv'.format(resolution), fn):
                continue
            path = os.path.join(csv_dir, fn)
            dfs.append(pd.read_csv(path, comment='#'))
        df = clean_column_names(pd.concat(dfs), {
                DATETIME_ISO8601: DATETIME
            })
        df[DATETIME] = pd.to_datetime(df[DATETIME])
        df.index = df[DATETIME]
        return df
    def to_dataframe(self):
        return self.df
    def gps_models(self):
        models = []
        for name in self.df.columns:
            m = re.match('gps_([a-z0-9]+)_latitude', name)
            if m:
                models.append(m.group(1))
        return models
    def lat_lon_columns(self, gps_model=None):
        if gps_model is None:
            gps_model = self.gps_models()[0]
        lat_col = 'gps_{}_latitude'.format(gps_model)
        lon_col = 'gps_{}_longitude'.format(gps_model)
        return lat_col, lon_col

class _ArmstrongParser(object):
    def __init__(self, csv_dir):
        self.df = self.parse(csv_dir)
    def parse(self, csv_dir, resolution=60):
        assert resolution == 60, 'unsupported resolution {}'.format(resolution)
        REGEX = r'AR\d+\d{4}_\d{4}.csv'
        dfs = []
        for f in os.listdir(csv_dir):
            if re.match(REGEX, f):
                df = pd.read_csv(os.path.join(csv_dir, f), skiprows=1, na_values=[' NAN', ' NODATA'])
                dfs.append(df)     
        df = clean_column_names(pd.concat(dfs, ignore_index=True))
        df.insert(0, DATETIME, date_time_to_datetime(df.pop('date_gmt'), df.pop('time_gmt')))
        df.index = df[DATETIME]
        return df
    def to_dataframe(self):
        return self.df   
    def lat_lon_columns(self, **kw):
        if 'gps_model' in kw and kw['gps_model'] is not None:
            warnings.warn('specifying GPS model for Armstrong data has no effect')
        return 'dec_lat', 'dec_lon'

class Underway(object):
    def __init__(self, cruise, resolution=60, raw_directory=None): 
        resolv = Resolver()
        if raw_directory is None:
            csv_dir = resolv.raw_directory('underway', cruise)
        else:
            csv_dir = raw_directory
        self.cruise = cruise
        self.vessel = cruise_to_vessel(cruise)
        if self.vessel == ENDEAVOR:
            self.parser = _EndeavorParser(csv_dir, resolution)
        elif self.vessel == ARMSTRONG:
            self.parser = _ArmstrongParser(csv_dir)
        self.filename = '{}_underway'.format(self.cruise)
        self.product_file = resolv.product_file(UNDERWAY, cruise, self.filename)
        self.dt = None # cached datatable
    def from_dataframe(self, df):
        self.dt = data_table(df, filename=self.filename)
    def to_dataframe(self):
        if self.dt is not None:
            return self.dt
        df = self.parser.to_dataframe()
        df.index = range(len(df))
        self.dt = data_table(df, filename=self.filename)
        return self.dt
    # accessors
    def time_to_location(self, time, gps_model=None):
        """returns lat, lon given time. picks the most recent location relative
        to the given timestamp"""
        lat_col, lon_col = self.parser.lat_lon_columns(gps_model=gps_model)
        index = max(0, self.parser.df.index.searchsorted(pd.to_datetime(time)) - 1)
        row = self.parser.df.iloc[index]
        return row[lat_col], row[lon_col]
    def time_to_lat(self, time, gps_model=None):
        # convenience
        return self.time_to_location(time, gps_model)[0]
    def time_to_lon(self, time, gps_model=None):
        # convenience
        return self.time_to_location(time, gps_model)[1]
    def add_locations(self, df, time_column, lat_col, lon_col, gps_model=None):
        """given a dataframe with a datetime column and lat lon cols,
        fill in any NaNs in the lat/lon columns with the results of
        time_to_location"""
        assert time_column in df.columns, 'no such column {}'.format(time_column)
        assert lat_col in df.columns, 'no such column {}'.format(lat_col)
        assert lon_col in df.columns, 'no such column {}'.format(lon_col)
        assert len(df.index) == len(df.index.unique()), 'index must be unique'
        df = df.copy()
        mods = []
        for row in df.itertuples():
            ix = getattr(row, 'Index')
            dt = getattr(row, time_column)
            mods.append((ix, self.time_to_location(dt, gps_model)))
        for ix, (new_lat, new_lon) in mods:
            lat = df.at[ix, lat_col]
            lon = df.at[ix, lon_col]
            if np.isnan(lat) and np.isnan(lon):
                df.at[ix, lat_col] = new_lat
                df.at[ix, lon_col] = new_lon
        return df
