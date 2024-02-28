import pandas as pd
import numpy as np
import re

from .utils import dropna_except, clean_column_names, cast_columns, float_to_datetime, format_dataframe

"""Parsing chlorophyll Excel spreadsheet"""

def parse_chl(chl_xl_path):
    """Parse Sosik chl Excel spreadsheet"""
    raw = pd.read_excel(chl_xl_path, dtype={
            'Cast #': str,
        })
    # check for regression
    # assert set(raw.columns) == set(RAW_COLS), 'chl spreadsheet does not contain expected columns'
    # clean and rename columns
    df = clean_column_names(raw, {
        'Vol\nFilt': 'vol_filtered', # remove abbreviation
        'Chl (ug/l)': 'chl', # remove unit
        'Phaeo (ug/l)': 'phaeo', # remove unit
        '90% Acetone': 'ninety_percent_acetone' # remove leading digit
    })
    cols2delete = set()
    for c in df.columns:
        if c.startswith('unnamed_'):
            cols2delete.add(c)
    for c in cols2delete:
        df.pop(c)
    # cast the int columns
    df = df.astype({ 'filter_size': int })
    # convert floats like 20180905.0 to dates
    df['date'] = float_to_datetime(df['date'])
    df['cal_date'] = float_to_datetime(df['cal_date'])
    # cast all string columns
    str_cols = ['cast', 'niskin', 'sample']
    df = cast_columns(df, str, str_cols, fillna='')
    # deal with missing values in cast/niskin
    df['cast'] = df['cast'].str.replace(' +','',regex=True)
    df['cast'] = df['cast'].replace('',np.nan)
    df['niskin'] = df['niskin'].str.replace(' +','',regex=True)
    df['niskin'] = df['niskin'].replace('',np.nan)
    df = df.dropna(subset=['cast','niskin'])
    # deal with niskin numbers like 4/5/6 by picking first one
    df['niskin'] = df['niskin'].str.replace(r'/.*','',regex=True).astype(int)
    df['cast'] = df['cast'].astype(int)
    # deal with 'freeze' in time_in and time_out columns
    # add freeze column
    freeze = df['time_in'].astype(str).str.lower() == 'freeze'
    df['freeze'] = freeze
    # now parse time in and time out date cols
    for c in ['time_in', 'time_out']:
        df.loc[freeze, c] = np.nan
        # deal with whitespace-only time columns
        regex = re.compile(r'^ +$')
        df[c] = pd.to_datetime(df[c].astype(str).str.replace(regex,'',regex=True))
    df.filter_size = df.filter_size.astype(str)
    def fms_replace(value, replacement):
        df.filter_size = df.filter_size.replace(value, replacement)
    fms_replace('0','>0') # whole seawater
    fms_replace('10','<10') # we know < a priori
    fms_replace('5','>5') # we know > a priori
    fms_replace('20','>20') # we know > a priori
    return df

def subset_chl(parsed_chl):
    cols = ['cruise','cast','niskin','replicate','vol_filtered','filter_size',
        'tau_calibration','fd_calibration',
        'rb','ra','blank','rb_blank','ra_blank',
        'chl','phaeo','quality_flag']
    return parsed_chl[cols]

def merge_bottle_summary(chl, bottle_summary):
    chl = chl.copy()
    bottle_summary = bottle_summary.copy()
    chl.cast = chl.cast.astype(str)
    chl.niskin = chl.niskin.astype(int)
    bottle_summary.cast = bottle_summary.cast.astype(str).str.lstrip("0")  #remove leading 0s for merge
    bottle_summary.niskin = bottle_summary.niskin.astype(int)
    chl = chl.merge(bottle_summary, on=['cruise','cast','niskin'], how='left')
    chl = chl.dropna(subset=['cruise'])
    return chl

def parse_ryn_chl(chl_xl_path):
    # read Excel file
    df = pd.read_excel(chl_xl_path, dtype = {
        'Cast #': str, # use str type for cast / niskin
        'Niskin #': str
    })
     # clean column names
    ryn_chl = clean_column_names(df, {
        'Vol Filt (ml)': 'vol_filtered', # remove abbreviation
        'Filter Mesh\nSize (µm)': 'filter_mesh_size',
        'Chl (ug/l)': 'chl', # remove unit
        'Phaeo (ug/l)': 'phaeo', # remove unit
        'Unnamed: 29': 'comments_2', # give descriptive name
        '90% Acetone': 'ninety_percent_acetone' # remove leading digit
    })
    # these dates get parsed as floating point or integers, parse as date
    ryn_chl['date'] = pd.to_datetime(ryn_chl['date'].astype(int).astype(str))
    # clean up variants of filter mesh size
    ryn_chl['filter_mesh_size'] = ryn_chl['filter_mesh_size'].replace('> 5', '>5')
    ryn_chl['filter_mesh_size'] = ryn_chl['filter_mesh_size'].replace('> 20', '>20')
    # drop nas
    ryn_chl_clean = dropna_except(ryn_chl, ['comments'])
    return ryn_chl_clean

def format_chl(df):
    """format parsed chl spreadsheet"""
    return format_dataframe(df, precision={
        'ra': 2,
        'rb': 2,
        })
