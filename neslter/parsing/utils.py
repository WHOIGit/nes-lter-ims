import re

import numpy as np
import pandas as pd

# spreadsheet cleaning and formatting

def clean_column_name(colname):
    """convert column names to lowercase with underbars"""
    colname = colname.lower()
    colname = re.sub(r'[^a-z0-9_]+','_',colname) # sub _ for nonalpha chars
    colname = re.sub(r'_$','',colname)  # remove trailing _
    colname = re.sub(r'^([0-9])',r'_\1',colname) # insert _ before leading digit
    return colname

def clean_column_names(df, col_map={}):
    """clean all column names for a Pandas dataframe,
    in place"""
    ccns = []
    for c in df.columns:
        if c in col_map:
            ccns.append(col_map[c])
        else:
            ccns.append(clean_column_name(c))
    df.columns = ccns

def drop_columns(df, columns):
    """drop a list of columns from a Pandas dataframe,
    in place"""
    for c in columns:
        df.pop(c)

def dropna_except(df, except_subset):
    """drop rows containing nans from a Pandas dataframe,
    but allow nans in the specified subset of columns,
    in place"""
    subset = set(df.columns)
    for ec in except_subset:
        subset.remove(ec)
    df.dropna(inplace=True, subset=subset)

def cast_columns(df, dtype, columns):
    """convert columns in a dataframe to the given datatype,
    in place"""
    for c in columns:
        df[c] = df[c].astype(dtype)

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