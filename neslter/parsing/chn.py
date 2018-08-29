import pandas as pd

from .utils import clean_column_names, dropna_except, format_dataframe

DATE_COLS = ['date_combusted', 'date_run']

def parse_chn(chn_xl_path):
    df = pd.read_excel(chn_xl_path)
    clean_column_names(df)
    dropna_except(df, ['notes'])
    for col in DATE_COLS:
       df[col] = pd.to_datetime(df[col], format='%Y%m%d')
    return df

def format_chn(df):
    df = format_dataframe(df, precision={
        'umol_n': 2,
        'umol_c': 2
        })
    return df