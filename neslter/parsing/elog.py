import os

import numpy as np
import pandas as pd
import re

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

class EventLog(object):
    def __init__(self, df=None):
        if df is not None:
            self.df = df.copy()
    @staticmethod
    def parse(path):
        elog = EventLog()
        elog.df = parse_elog(path)
        return elog
    @staticmethod
    def process(elog_path, hdr_dir=None, toi_path=None):
        e = EventLog.parse(elog_path)
        if toi_path is not None:
            e = e.add_events(clean_toi_discrete(toi_path))
        if hdr_dir is not None:
            e = e.merge_ctd_comments(hdr_dir)
        e = e.fix_incubation_cast_numbers()
        return e
    def add_events(self, events):
        new_df = pd.concat([self.df, events]).sort_values(DATETIME)
        return EventLog(new_df)
    def remove_recover_events(self, instrument):
        new_df = self.df[~((self.df[INSTRUMENT] == instrument) & (self.df[ACTION] == 'recover'))]
        return EventLog(new_df)
    def remove_instrument(self, instrument):
        new_df = self.df[~(self.df[INSTRUMENT] == instrument)]
        return EventLog(new_df)
    def remove_ctd_recoveries(self):
        return self.remove_recover_events(CTD_INSTRUMENT)
    def ctd_events(self):
        ctd = self.events_for_instrument(CTD_INSTRUMENT).copy()
        ctd[CAST] = ctd[CAST].map(cast_to_int)
        return ctd
    def to_dataframe(self):
        return self.df
    # accessors
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
        return self.stations().loc[cast]
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
    def fix_incubation_cast_numbers(self):
        df = self.df.copy()
        slic = (df[INSTRUMENT] == INCUBATION) & ~(df[CAST].isna())
        df.loc[slic, CAST] = df.loc[slic, CAST].str.replace('C','').astype(int)
        return EventLog(df)
    def merge_ctd_comments(self, hdr_dir):
        hdr = self.parse_ctd_hdrs(hdr_dir)
        e = self.remove_ctd_recoveries()
        ctd = e.ctd_events()
        # now merge comments
        comments = hdr.merge(ctd, on='Cast')[['Cast','Comment_y']].drop_duplicates()
        comments = comments[~(comments['Comment_y'].isna())]
        merged = hdr.merge(comments, on='Cast', how='left')
        merged['Comment'] = merged.pop('Comment_y')
        return e.remove_instrument(CTD_INSTRUMENT).add_events(merged)

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
