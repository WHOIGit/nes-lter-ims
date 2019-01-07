import os

import pandas as pd
import re

# keys
EN608='En608'
EN617='En617'

INSTRUMENT = 'Instrument'
ACTION = 'Action'
COMMENT = 'Comment'
STATION = 'Station'
CAST = 'Cast'
DATETIME = 'dateTime8601'
LAT='Latitude'
LON='Longitude'

PUMP_TYPE = 'pump_type'
TOI_DISCRETE = 'TOI discrete'
UNDERWAY_SCIENCE_SEAWATER = 'Underway Science seawater'
USS_IMPELLER = 'Underway Science seawater impeller'
USS_DIAPHRAGM = 'Underway Science seawater diaphragm pump'

IMPELLER_PUMP = 'impeller pump'
DIAPHRAGM_PUMP = 'diaphragm pump'

COLUMNS = [DATETIME, INSTRUMENT, ACTION, STATION, CAST, LAT, LON, COMMENT]

# parse elog and clean columns / column names

def parse_elog(elog_path):
    assert os.path.exists(elog_path), 'elog file not found at {}'.format(elog_path)
    df = pd.read_csv(elog_path) # defaults work
    df[DATETIME] = pd.to_datetime(df[DATETIME]) # parse date column
    df = df[COLUMNS] # retain only the columns we want to use
    df = df.sort_values(DATETIME) # sort by time
    return df

def remove_recover_events(elog, instrument):
    return elog[~((elog[INSTRUMENT] == instrument) & (elog[ACTION] == 'recover'))]

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
    if cruise == EN608:
        # for en608 the 'instrument' is always underway science seawater
        # with no indiciation of pump type, so include pump type in comment field
        log[INSTRUMENT] = UNDERWAY_SCIENCE_SEAWATER
        log[COMMENT] = log[PUMP_TYPE].replace({
            0: IMPELLER_PUMP,
            1: DIAPHRAGM_PUMP
        })
    elif cruise == EN617:
        # for en617 there are two 'instruments', one for the impeller pump
        # and one for the diaphragm pump, so use them
        log[INSTRUMENT] = log[PUMP_TYPE].replace({
            0: USS_IMPELLER,
            1: USS_DIAPHRAGM,
        })
        log[COMMENT] = ''
    # station and cast are n/a to these samples       
    log[STATION] = ''
    log[CAST] = ''
    # retain only the columns we want to keep
    log = log[COLUMNS]
    return log