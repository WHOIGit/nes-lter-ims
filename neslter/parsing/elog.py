import os
from glob import glob

import numpy as np
import pandas as pd
import re

from .utils import data_table

from neslter.parsing.files import Resolver
from neslter.parsing.ctd.hdr import compile_hdr_files
from neslter.parsing.underway import Underway

from neslter.parsing.files import DataNotFound

# keys

INSTRUMENT = 'Instrument'
ACTION = 'Action'
COMMENT = 'Comment'
STATION = 'Station'
CAST = 'Cast'
DATETIME = 'dateTime8601'
LAT='Latitude'
LON='Longitude'
MESSAGE_ID = 'Message ID'

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

ELOG_COLUMNS = [MESSAGE_ID, DATETIME, INSTRUMENT, ACTION, STATION, CAST, LAT, LON, COMMENT]
COLUMNS_WO_MESSAGE_ID = [DATETIME, INSTRUMENT, ACTION, STATION, CAST, LAT, LON, COMMENT]

def elog_path(cruise):
    elog_dir = Resolver().raw_directory('elog', cruise)
    candidates = glob(os.path.join(elog_dir, 'R2R_ELOG_*_FINAL_EVENTLOG*.csv'))
    if len(candidates) != 1:
         raise DataNotFound ('cannot find event log at {}'.format(elog_dir))
    return candidates[0]

def hdr_path(cruise):
    try:
        return Resolver().raw_directory('ctd', cruise)
    except KeyError:
        return None

def sidecar_file_path(cruise, filename):
    try:
        elog_dir = Resolver().raw_directory('elog', cruise)
    except KeyError:
        return None
    path = os.path.join(elog_dir, filename)
    if not os.path.exists(path):
        return None
    return path

def toi_path(cruise):
    filename = '{}_TOI_underwaysampletimes.txt'.format(cruise.capitalize())
    return sidecar_file_path(cruise, filename)

def corrections_path(cruise):
    filename = 'R2R_ELOG_{}_corrections.xlsx'.format(cruise)
    return sidecar_file_path(cruise, filename)

def additions_path(cruise):
    filename = 'R2R_ELOG_{}_additions.xlsx'.format(cruise)
    return sidecar_file_path(cruise, filename)

class EventLog(object):
    def __init__(self, cruise):
        self.cruise = cruise
        self.parse(cruise)
    def parse(self, cruise):
        ep = elog_path(cruise)
        self.df = parse_elog(ep)
        corr_path = corrections_path(cruise)
        if corr_path is not None:
            self.apply_corrections(corr_path)
        addns_path = additions_path(cruise)
        if addns_path is not None:
            self.apply_additions(addns_path)
        hdr_dir = hdr_path(cruise)
        tp = toi_path(cruise)
        if tp is not None:
            self.remove_action(TOI_DISCRETE)
            self.add_events(clean_toi_discrete(tp))
        if hdr_dir is not None:
            self.add_ctd_deployments(hdr_dir)
        self.add_underway_locations()
        self.fix_incubation_cast_numbers()
    def add_events(self, events):
        self.df = pd.concat([self.df, events], sort=True).sort_values(DATETIME)
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
    def add_ctd_deployments(self, hdr_dir):
        self.remove_ctd_recoveries()
        hdr = self.parse_ctd_hdrs(hdr_dir)
        self.remove_instrument(CTD_INSTRUMENT)
        self.add_events(hdr)
    def apply_corrections(self, corr_path):
        corr = pd.read_excel(corr_path)
        corr[DATETIME] = pd.to_datetime(corr[DATETIME], utc=True)
        corr.pop('Instrument')
        corr.pop('Action')
        merged = self.df.merge(corr, on=MESSAGE_ID, how='left')
        DATETIME_X = '{}_x'.format(DATETIME)
        DATETIME_Y = '{}_y'.format(DATETIME)
        merged[DATETIME] = pd.to_datetime(merged[DATETIME_Y].combine_first(merged[DATETIME_X]), utc=True)
        self.df = merged
    def apply_additions(self, addns_path):
        addns = pd.read_excel(addns_path)
        # passing `format='ISO8601'` fixes EN668 addition file datetime format inconsistencies
        # if your strings are all ISO8601 but not necessarily in exactly the same format
        addns[DATETIME] = pd.to_datetime(addns[DATETIME], utc=True, format="ISO8601")
        # add placeholder columns
        addns.insert(4, 'Longitude', np.nan)
        addns.insert(4, 'Latitude', np.nan)
        addns.insert(4, 'Cast', np.nan)
        self.df = pd.concat([self.df, addns])
    def fix_en627_cast_numbers(self):
        pass
    def add_underway_locations(self):
        try:
            uw = Underway(self.cruise)
        except:
            raise
        try:
            uw_lat = self.df[DATETIME].map(lambda t: uw.time_to_lat(t))
            uw_lon = self.df[DATETIME].map(lambda t: uw.time_to_lon(t))
            #self.df[LAT] = self.df[LAT].combine_first(uw_lat)
            #self.df[LON] = self.df[LON].combine_first(uw_lon)
            self.df[LAT] = uw_lat
            self.df[LON] = uw_lon
        except:
            pass # FIXME need to address issues with Sharp underway data
    def to_dataframe(self):
        self.df.index = range(len(self.df))
        self.df = self.df.sort_values(DATETIME)
        self.df = self.df[ELOG_COLUMNS]
        filename = '{}_elog'.format(self.cruise)
        return data_table(self.df, filename=filename)
    # accessors
    def events_for_instrument(self, instrument):
        return self.df[self.df[INSTRUMENT] == instrument]
    def stations(self):
        ctdf = self.events_for_instrument(CTD_INSTRUMENT)
        casts = ctdf[CAST]
        stations = ctdf[STATION]
        stations.index = casts
        return stations
    def casts(self):
        return self.stations().index
    def cast_to_station(self, cast):
        """return the station, given the cast"""
        cast_len = self.stations().index.astype(str).str.len()  
        try:
            # convert integer casts to strings and add leading zeros, i.e. ar34b
            cast = str(cast).zfill(cast_len[0])
        except:
            pass
        # handle data types: int, str, float, nan   
        try:
            station_data = self.stations().loc[cast] 
            try: 
                if not station_data.empty: 
                    return station_data.values[0]
                else: 
                    return np.nan
            except:
                return np.nan
        except AttributeError:
            if not pd.isna(station_data):
                try:
                    return self.stations().loc[cast].values[0]
                except:
                    return np.nan
            else: 
                return np.nan
        except KeyError:
            return np.nan

    # parse hdr files to generate CTD deploy events
    def parse_ctd_hdrs(self, hdr_dir):
        if (not os.path.exists(hdr_dir)):
            raise DataNotFound('CTD hdr directory not found at {}'.format(hdr_dir))
        hdr = compile_hdr_files(hdr_dir)
        hdr = hdr[['date','cast','latitude','longitude']]
        hdr.insert(1, 'Station', hdr['cast'].map(lambda c: self.cast_to_station(c)))
        hdr.insert(1, 'Action', 'deploy')
        hdr.insert(1, 'Instrument', 'CTD911')
        hdr.insert(7, 'Comment', np.nan)
        hdr.columns = COLUMNS_WO_MESSAGE_ID
        return hdr

# parse elog and clean columns / column names

def parse_elog(elog_path):
    if (not os.path.exists(elog_path)):
        raise DataNotFound('elog file not found at {}'.format(elog_path))
    df = pd.read_csv(elog_path, dtype={
        CAST: str
    })
    df[DATETIME] = pd.to_datetime(df[DATETIME], utc=True) # parse date column
    df = df[ELOG_COLUMNS] # retain only the columns we want to use
    df = df.sort_values(DATETIME) # sort by time
    df.index = df[MESSAGE_ID].values
    return df


# parse and clean oxygen isotope data

def parse_toi_discrete(toi_path):
    # parse TOI discrete text file
    df = pd.read_csv(toi_path, sep='\s\s+', engine='python')
    df.columns = [DATETIME, PUMP_TYPE, LAT, LON, 'ignore']
    df.pop('ignore')
    # add the action column
    df[ACTION] = TOI_DISCRETE
    # parse datetimes
    df[DATETIME] = pd.to_datetime(df[DATETIME], utc=True)
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
    log = log[COLUMNS_WO_MESSAGE_ID]
    return log
