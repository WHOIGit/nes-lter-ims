import pandas as pd

from .utils import clean_column_names

def parse_sample_log(path):
    df = pd.read_excel(path)
    return clean_column_names(df)