import os
from glob import glob

import pandas as pd

from neslter.parsing.files import DataNotFound

from ..utils import clean_column_names
from .common import pathname2cruise_cast

def parse_asc_csv(asc_path, delimiter=';'):
    df = pd.read_csv(asc_path, encoding='latin-1', delimiter=delimiter)
    return df

def parse_asc_fwf(asc_path):
    # do some hacking to determine width of columns
    # first, read the file without the header to determine how many columns.
    # we can't do this from the header because in fixed-width files the
    # column names might not have any whitespace between them.
    # if this is the case for data values, this whole approach will fail
    df = pd.read_fwf(asc_path, skiprows=1, nrows=1, header=None, encoding='latin-1')
    n_cols = len(df.columns)  
    # now get the length of the first line which contains headers
    with open(asc_path, encoding='latin-1') as fin:
        for line in fin.readlines():
            break
    # assume all columns are the same width. determine that width
    line = line.rstrip()
    col_width = int(len(line) / n_cols)
    col_widths = [col_width for _ in range(n_cols)]
    # now parse the fixed-width format
    # Pandas will automatically append ".1" to any duplicate column name
    df = pd.read_fwf(asc_path, widths=col_widths, encoding='latin-1')
    return df

def parse_asc(asc_path, delimiter=','):
    # duck type to see if this is CSV or fixed-width
    df = parse_asc_csv(asc_path, delimiter)
    if len(df.columns) == 1: # whoops, try a different delimiter
        if delimiter == ',':
            delimiter = ';'
        elif delimiter == ';':
            delimiter = ','
        df = parse_asc_csv(asc_path, delimiter)
    if len(df.columns) == 1: # try fixed-width
        df = parse_asc_fwf(asc_path)
    df = clean_column_names(df)
    return df

def format_asc(df):
    return df.copy()

def list_casts(asc_dir):
    for p in sorted(glob(os.path.join(asc_dir, '*.asc'))):
        b = os.path.basename(p)
        cruise, fcast = pathname2cruise_cast(b)
        if cruise is None or fcast is None:
            continue
        cast = int(fcast)
        yield (cruise, cast)

def parse_cast(asc_dir, cast=1, delimiter=';'):
    for p in sorted(glob(os.path.join(asc_dir, '*.asc'))):
        b = os.path.basename(p)
        cruise, fcast = pathname2cruise_cast(b)
        if cruise is None or fcast is None: # bad filename, skip
            continue
        try:
            if int(cast) == int(fcast):
                df = parse_asc(p, delimiter)
                df.insert(0, 'cast', cast)
                df.insert(0, 'cruise', cruise)
                return df
        except ValueError:
            if (cast.lstrip("0") == fcast.lstrip("0")):
                df = parse_asc(p, delimiter)
                df.insert(0, 'cast', cast)
                df.insert(0, 'cruise', cruise)
                return df

    raise DataNotFound('cast not found: {}'.format(cast))
