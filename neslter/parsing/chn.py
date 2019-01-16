import pandas as pd

from .utils import clean_column_names, dropna_except, format_dataframe

RAW_COLS = ['Cruise', 'Cast', 'Niskin', 'CHN_Name', 'Replicate', 'Sample Tray ID',
       'Date_Combusted', 'Date_Run', 'Foil Packet', 'umol N', 'umol C',
       'Notes:']

DATE_COLS = ['date_combusted', 'date_run']

def parse_chn(chn_xl_path):
    df = pd.read_excel(chn_xl_path)
    assert set(df.columns) == set(RAW_COLS), 'chn spreadsheet does not contain expected columns'
    df = clean_column_names(df)
    df = dropna_except(df, ['notes'])
    for col in DATE_COLS:
       df[col] = pd.to_datetime(df[col], format='%Y%m%d')
    df = df.astype({ 'cast': int, 'niskin': int }) # cast to int to remove decimal notation
    df['notes'] = df['notes'].fillna('')
    return df

def format_chn(df):
    df = format_dataframe(df, precision={
        'umol_n': 2,
        'umol_c': 2
        })
    return df