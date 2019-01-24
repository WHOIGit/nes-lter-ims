import os
from glob import glob

import numpy as np
import pandas as pd
import re

from .utils import data_table

from neslter.parsing.files import Resolver
from neslter.parsing.ctd.hdr import compile_hdr_files

# keys

INSTRUMENT = 'Instrument'
ACTION = 'Action'
COMMENT = 'Comment'
STATION = 'Station'
CAST = 'Cast'
DATETIME = 'dateTime8601'
LAT='Latitude'
LON='Longitude'

RECOVER_ACTION = 'recover'

EN608='en608'
EN617='en617'

IMPELLER_PUMP = 'impeller pump'
DIAPHRAGM_PUMP = 'diaphragm pump'
INCUBATION = 'Incubation'

PUMP_TYPE = 'pump_type'
TOI_DISCRETE = 'TOI discrete'
UNDERWAY_SCIENCE_SEAWATER = 'Underway Science seawater'
USS_IMPELLER = 'Underway Science seawater impeller'
USS_DIAPHRAGM = 'Underway Science seawater diaphragm pump'
CTD_INSTRUMENT = 'CTD911'

COLUMNS = [DATETIME, INSTRUMENT, ACTION, STATION, CAST, LAT, LON, COMMENT]

def elog_path(cruise):
    elog_dir = Resolver().raw_directory('elog', cruise)
    candidates = glob(os.path.join(elog_dir, 'R2R_ELOG_*.csv'))
    assert len(candidates) == 1
    return candidates[0]

def hdr_path(cruise):
    try:
        return Resolver().raw_directory('ctd', cruise)
    except KeyError:
        return None

def toi_path(cruise):
    try:
        elog_dir = Resolver().raw_directory('elog', cruise)
    except KeyError:
        return None
    filename = '{}_TOI_underwaysampletimes.txt'.format(cruise.capitalize())
    path = os.path.join(elog_dir, filename)
    if not os.path.exists(path):
        return None
    return path

class EventLog(object):
    def __init__(self, cruise):
        self.parse(cruise)
        self.cruise = cruise
    def parse(self, cruise):
        ep = elog_path(cruise)
        self.df = parse_elog(ep)
        hdr_dir = hdr_path(cruise)
        tp = toi_path(cruise)
        if tp is not None:
            self.remove_action(TOI_DISCRETE)
            self.add_events(clean_toi_discrete(tp))
        if hdr_dir is not None:
            self.merge_ctd_comments(hdr_dir)
        self.fix_incubation_cast_numbers()
    def add_events(self, events):
        self.df = pd.concat([self.df, events]).sort_values(DATETIME)
    def remove_recover_events(self, instrument):
        self.remove_action(RECOVER_ACTION, instrument)
    def remove_instrument(self, instrument):
        self.df = self.df[~(self.df[INSTRUMENT] == instrument)]
    def remove_action(self, action, instrument=None):
        new_df = self.df.copy()
        if instrument is not None:
            new_df = new_df[~((new_df[ACTION] == action) & (new_df[INSTRUMENT] == instrument))]
        else:
            new_df = new_df[new_df[ACTION] != action]
        self.df = new_df
    def remove_ctd_recoveries(self):
        self.remove_recover_events(CTD_INSTRUMENT)
    def fix_incubation_cast_numbers(self):
        df = self.df.copy()
        slic = (df[INSTRUMENT] == INCUBATION) & ~(df[CAST].isna())
        df.loc[slic, CAST] = df.loc[slic, CAST].astype('str').str.replace('C','').astype(int)
        self.df = df
    def merge_ctd_comments(self, hdr_dir):
        hdr = self.parse_ctd_hdrs(hdr_dir)
        self.remove_ctd_recoveries()
        ctd = self.ctd_events()
        # now merge comments
        comments = hdr.merge(ctd, on='Cast')[['Cast','Comment_y']].drop_duplicates()
        comments = comments[~(comments['Comment_y'].isna())]
        merged = hdr.merge(comments, on='Cast', how='left')
        merged['Comment'] = merged.pop('Comment_y')
        self.remove_instrument(CTD_INSTRUMENT)
        self.add_events(merged)
    def to_dataframe(self):
        self.df.index = range(len(self.df))
        filename = '{}_elog'.format(self.cruise)
        return data_table(self.df, filename=filename)
    # accessors
    def ctd_events(self):
        ctd = self.events_for_instrument(CTD_INSTRUMENT).copy()
        ctd[CAST] = ctd[CAST].map(cast_to_int)
        return ctd
    def events_for_instrument(self, instrument):
        return self.df[self.df[INSTRUMENT] == instrument]
    def stations(self):
        ctdf = self.events_for_instrument(CTD_INSTRUMENT)
        casts = ctdf[CAST].map(cast_to_int)
        stations = ctdf[STATION]
        stations.index = casts
        return stations
    def casts(self):
        return self.stations().index
    def cast_to_station(self, cast):
        """return the station, given the cast"""
        if cast in self.stations().index:
            return self.stations().loc[cast]
        else:
            return np.nan()
    # parse hdr files to generate CTD deploy events
    def parse_ctd_hdrs(self, hdr_dir):
        assert os.path.exists(hdr_dir), 'CTD hdr directory not found at {}'.format(hdr_dir)
        hdr = compile_hdr_files(hdr_dir)
        hdr = hdr[['date','cast','latitude','longitude']]
        hdr.insert(1, 'Station', hdr['cast'].map(lambda c: self.cast_to_station(c)))
        hdr.insert(1, 'Action', 'deploy')
        hdr.insert(1, 'Instrument', 'CTD911')
        hdr.insert(7, 'Comment', np.nan)
        hdr.columns = COLUMNS
        return hdr

# parse elog and clean columns / column names

def parse_elog(elog_path):
    assert os.path.exists(elog_path), 'elog file not found at {}'.format(elog_path)
    df = pd.read_csv(elog_path) # defaults work
    df[DATETIME] = pd.to_datetime(df[DATETIME]) # parse date column
    df = df[COLUMNS] # retain only the columns we want to use
    df = df.sort_values(DATETIME) # sort by time
    return df

def cast_to_int(cast):
    """given a string naming a cast, remove non-alpha characters and parse as int"""
    try:
        return int(re.sub('^[^0-9]+','',cast))
    except:
        raise ValueError('cannot interpret cast {} as an integer'.format(cast))

# parse and clean oxygen isotope data

def parse_toi_discrete(toi_path):
    # parse TOI discrete text file
    df = pd.read_csv(toi_path, sep='\s\s+', engine='python')
    df.columns = [DATETIME, PUMP_TYPE, LAT, LON, 'ignore']
    df.pop('ignore')
    # add the action column
    df[ACTION] = TOI_DISCRETE
    # parse datetimes
    df[DATETIME] = pd.to_datetime(df[DATETIME])
    return df

def clean_toi_discrete(toi_path):
    log = parse_toi_discrete(toi_path)
    # infer cruise from filename, e.g.,
    # 'En608_TOI_underwaysampletimes.txt'
    cruise_match = re.match(r'([^_]+)_.*', os.path.basename(toi_path))
    # handle cruise-specific issues
    if cruise_match:
        cruise = cruise_match.group(1)
    else:
        cruise = None
    if cruise == EN608.capitalize():
        # for en608 the 'instrument' is always underway science seawater
        # with no indiciation of pump type, so include pump type in comment field
        log[INSTRUMENT] = UNDERWAY_SCIENCE_SEAWATER
        log[COMMENT] = log[PUMP_TYPE].replace({
            1: IMPELLER_PUMP,
            0: DIAPHRAGM_PUMP
        })
    elif cruise == EN617.capitalize():
        # for en617 there are two 'instruments', one for the impeller pump
        # and one for the diaphragm pump, so use them
        log[INSTRUMENT] = log[PUMP_TYPE].replace({
            1: USS_IMPELLER,
            0: USS_DIAPHRAGM,
        })
        log[COMMENT] = ''
    # station and cast are n/a to these samples       
    log[STATION] = ''
    log[CAST] = ''
    # retain only the columns we want to keep
    log = log[COLUMNS]
    return log
