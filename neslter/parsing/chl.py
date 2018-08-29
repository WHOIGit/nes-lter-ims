import pandas as pd

from .utils import clean_column_names, drop_columns, dropna_except, cast_columns

"""Parsing chlorophyll Excel spreadsheet"""

# columns expected
CHL_COLUMNS = ['Cruise #:', 'Cast #', 'Niskin #', 'Target\nDepth', 'Replicate',
       'Filter\nSize', 'Vol\nFilt', 'Vol Extracted', 'Sample', '90% Acetone',
       'Dilution During Reading', 'Chl_Cal_Filename', 'tau_Calibration',
       'Fd_Calibration', 'Rb', 'Ra', 'blank', 'Rb-blank', 'Ra-blank',
       'Chl (ug/l)', 'Phaeo (ug/l)', 'Cal_Date', 'Fluorometer',
       'Lab notebook and page number', 'Comments', 'Sample.1',
       '90% Acetone.1']

def parse_chl(chl_xl_path):
    df = pd.read_excel(chl_xl_path)
    assert set(df.columns) == set(CHL_COLUMNS), 'chl spreadsheet does not contain expected columns'
    # clean column names
    clean_column_names(df, {
        'Vol\nFilt': 'vol_filtered', # unabbreviating to be consistent with vol_extracted
        '90% Acetone': 'ninety_percent_acetone', # spell initial number
        'Chl (ug/l)': 'chl', # remove units
        'Phaeo (ug/l)': 'phaeo', # remove units
        })
    # from now on, clean column names will be used
    # drop unused columns
    drop_columns(df, ['sample_1', '_90_acetone_1', 'fluorometer'])
    # drop nas
    dropna_except(df, ['comments'])
    # convert selected columns to ints
    int_cols = ['cast','niskin','target_depth','filter_size',
        'vol_filtered','vol_extracted','sample','ninety_percent_acetone']
    cast_columns(df, int, int_cols)
    return df