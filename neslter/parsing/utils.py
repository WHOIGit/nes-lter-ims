import re

import numpy as np
import pandas as pd

# spreadsheet cleaning and formatting

def clean_column_name(colname):
    """convert column names to lowercase with underbars"""
    colname = colname.lower().rstrip().lstrip()
    colname = re.sub(r'[^a-z0-9_]+','_',colname) # sub _ for nonalpha chars
    colname = re.sub(r'_$','',colname)  # remove trailing _
    colname = re.sub(r'^([0-9])',r'_\1',colname) # insert _ before leading digit
    return colname

def clean_column_names(df, col_map={}, inplace=False):
    """clean all column names for a Pandas dataframe"""
    if not inplace:
        df = df.copy()
    ccns = []
    for c in df.columns:
        if c in col_map:
            ccns.append(col_map[c])
        else:
            ccns.append(clean_column_name(c))
    df.columns = ccns
    return df

def drop_columns(df, columns, inplace=False):
    """drop a list of columns from a Pandas dataframe,
    in place"""
    if not inplace:
        df = df.copy()
    for c in columns:
        df.pop(c)
    return df

def dropna_except(df, except_subset, inplace=False):
    """drop rows containing nans from a Pandas dataframe,
    but allow nans in the specified subset of columns,
    in place"""
    subset = set(df.columns)
    for ec in except_subset:
        subset.remove(ec)
    df = df.dropna(inplace=inplace, subset=subset)
    return df

def cast_columns(df, dtype, columns, inplace=False, fillna=None):
    """convert columns in a dataframe to the given datatype,
    in place"""
    if not inplace:
        df = df.copy()
    for c in columns:
        if fillna is not None:
            df[c] = df[c].fillna(fillna)
        df[c] = df[c].astype(dtype)
    return df

def float_to_datetime(s, format='%Y%m%d'):
    """pandas will interpret some datetime formats as floats, e.g.,
    '20180830' will be parsed as the float 20180830.0.
    convert back to datetimes"""
    def convert(value):
        return pd.to_datetime(str(int(value)), format=format)
    return s.map(convert, na_action='ignore')
    # return pd.to_datetime(s.astype(int).astype(str), format=format)

def doy_to_datetime(doy, year, zero_based=False):
    """convert a decimal day of year (e.g., 34.58275) to a datetime.
    Day is one-based unless zero_based param is True"""
    origin = '{}-01-01'.format(year)
    o = pd.Timestamp(origin)
    if not zero_based:
        adjusted_doy = doy - 1
    return pd.to_datetime(adjusted_doy, unit='D', origin=o)

def datetime_to_rfc822(dt, include_dow=False):
    dow = '%a, ' if include_dow else ''
    fmt = '{}%d %b %Y %H:%M:%S %z'.format(dow)
    return dt.strftime(fmt)

def date_time_to_datetime(date, time):
    try:
        # for Series objects (e.g., DataFrame columns)
        return pd.to_timedelta(time.astype(str)) + pd.to_datetime(date)
    except AttributeError:
        # for a single date/time
        return pd.to_timedelta(time) + pd.to_datetime(date)

def format_floats(floats, precision=3, nan_string='NaN'):
    """convert an iterable of floating point numbers to
    formatted, fixed-precision strings"""
    result = []
    fmt = r'{{:.{}f}}'.format(precision)
    for n in floats:
        if np.isnan(n):
            result.append(nan_string)
        else:
            result.append(fmt.format(n))
    return result

def format_dataframe(df, precision={}, nan_string='NaN'):
    """format a dataframe, with control over floating point precision
    and representation of nans. returns a copy of the dataframe"""
    df = df.copy()
    for col, prec in precision.items():
        df[col] = format_floats(df[col], prec, nan_string=nan_string)
    # FIXME deal with int missing values
    # FIXME deal with string missing values
    return df

# pandas utilities

def delete_row(df, ix):
    df = df.copy()
    return df[df.index != ix]

def update_cell(df, ix, col, new_value):
    df = df.copy()
    df.at[ix, col] = new_value
    return df