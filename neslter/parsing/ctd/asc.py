import pandas as pd

from ..utils import clean_column_names

def parse_asc(asc_path, delimiter=';'):
    df = pd.read_csv(asc_path, encoding='latin-1', delimiter=delimiter)
    clean_column_names(df)
    return df

def format_asc(df):
    return df.copy()