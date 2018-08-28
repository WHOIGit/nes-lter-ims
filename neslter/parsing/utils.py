import re

import pandas as pd

# spreadsheet cleaning

def clean_column_name(colname):
    """convert column names to lowercase with underbars"""
    colname = colname.lower()
    colname = re.sub(r'[^a-z0-9_]+','_',colname) # sub _ for nonalpha chars
    colname = re.sub(r'_$','',colname)  # remove trailing _
    colname = re.sub(r'^([0-9])',r'_\1',colname) # insert _ before leading digit
    return colname

def clean_column_names(df, col_map={}):
    """clean all column names for a Pandas dataframe"""
    ccns = []
    for c in df.columns:
        if c in col_map:
            ccns.append(col_map[c])
        else:
            ccns.append(clean_column_name(c))
    df.columns = ccns

def drop_columns(df, columns):
    """drop a list of columns from a Pandas dataframe"""
    for c in columns:
        df.pop(c)

def dropna_except(df, except_subset):
    """drop rows containing nans from a Pandas dataframe,
    but allow nans in the specified subset of columns"""
    subset = set(df.columns)
    for ec in except_subset:
        subset.remove(ec)
    df.dropna(inplace=True, subset=subset)

def cast_columns(df, dtype, columns):
    """convert columns in a dataframe to the given datatype"""
    for c in columns:
        df[c] = df[c].astype(dtype)

def format_floats(floats, significant_digits=3, na_string='NaN'):
    """convert an iterable of floating point numbers to
    formatted, fixed-precision strings"""
    result = []
    fmt = r'{{:.{}f}}'.format(significant_digits)
    for n in floats:
        if np.isnan(n):
            result.append(na_string)
        else:
            result.append(fmt.format(n))
    return result