import pandas as pd
import numpy as np

from .utils import dropna_except, clean_column_names, cast_columns, float_to_datetime, format_dataframe

"""Parsing chlorophyll Excel spreadsheet"""

RAW_COLS = ['Cruise #:', 'Date', 'LTER\nStation', 'Cast #', 'Niskin #', 'Time\nIn',
       'Time\nOut', 'Replicate', 'Vol\nFilt', 'Filter\nSize', 'Vol Extracted',
       'Sample', '90% Acetone', 'Dilution During Reading', 'Chl_Cal_Filename',
       'tau_Calibration', 'Fd_Calibration', 'Rb', 'Ra', 'blank', 'Rb-blank',
       'Ra-blank', 'Chl (ug/l)', 'Phaeo (ug/l)', 'Cal_Date',
       'Personnel\nFilter', 'Personnel\nRead', 'Fluorometer', 'Comments',
       'Unnamed: 29']

def parse_chl(chl_xl_path):
    """Parse chl Excel spreadsheet"""
    raw = pd.read_excel(chl_xl_path, dtype={
            'Cast #': str,
        })
    # check for regression
    assert set(raw.columns) == set(RAW_COLS), 'chl spreadsheet does not contain expected columns'
    # clean and rename columns
    df = clean_column_names(raw, {
        'Vol\nFilt': 'vol_filtered', # remove abbreviation
        'Chl (ug/l)': 'chl', # remove unit
        'Phaeo (ug/l)': 'phaeo', # remove unit
        'Unnamed: 29': 'comments_2', # give descriptive name
        '90% Acetone': 'ninety_percent_acetone' # remove leading digit
    })
    # drop rows with nas
    na_allowed = ['lter_station', 'comments', 'comments_2', 'personnel_filter', 'personnel_read']
    df = dropna_except(df, na_allowed)
    # cast the int columns
    df = df.astype({ 'filter_size': int })
    # convert floats like 20180905.0 to dates
    df['date'] = float_to_datetime(df['date'])
    df['cal_date'] = float_to_datetime(df['cal_date'])
    # cast all string columns
    # it happens that all the cols where na is allowed are strings
    str_cols = na_allowed + ['cast', 'niskin', 'sample']
    df = cast_columns(df, str, str_cols, fillna='')
    # deal with 'freeze' in time_in and time_out columns
    # add freeze column
    freeze = df['time_in'].str.lower() == 'freeze'
    df['freeze'] = freeze
    # now parse time in and time out date cols
    for c in ['time_in', 'time_out']:
        df.loc[freeze, c] = np.nan
        df[c] = pd.to_datetime(df[c])
    # now split the replicate column. '10a' becomes 'a', '<10'
    # FIXME fix this in the original Excel file
    split_col = df.replicate.str.extract(r'(?P<filter_mesh_size>\d*)(?P<replicate>[abc])')
    def fms_replace(value, replacement):
        split_col.filter_mesh_size = split_col.filter_mesh_size.replace(value, replacement)
    fms_replace('','>0') # whole seawater
    fms_replace('10','<10') # we know < a priori
    fms_replace('5','>5') # we know > a priori
    fms_replace('20','>20') # we know > a priori
    df.replicate = split_col.replicate
    df['filter_mesh_size'] = split_col.filter_mesh_size
    return df

def format_chl(df):
    return format_dataframe(df, precision={
        'ra': 2,
        'rb': 2,
        })