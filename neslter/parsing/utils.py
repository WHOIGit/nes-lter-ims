import re
import os
import json

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
        return pd.to_datetime(str(int(value)), format=format, utc=True)
    return s.map(convert, na_action='ignore')
    # return pd.to_datetime(s.astype(int).astype(str), format=format)

def doy_to_datetime(doy, year, zero_based=False):
    """convert a decimal day of year (e.g., 34.58275) to a datetime.
    Day is one-based unless zero_based param is True"""
    origin = '{}-01-01'.format(year)
    o = pd.Timestamp(origin)
    if not zero_based:
        adjusted_doy = doy - 1
    return pd.to_datetime(adjusted_doy, unit='D', origin=o, utc=True)

def datetime_to_rfc822(dt, include_dow=False):
    dow = '%a, ' if include_dow else ''
    fmt = '{}%d %b %Y %H:%M:%S %z'.format(dow)
    return dt.strftime(fmt)

def date_time_to_datetime(date, time):
    try:
        # for Series objects (e.g., DataFrame columns)
        return pd.to_timedelta(time.astype(str)) + pd.to_datetime(date, utc=True)
    except AttributeError:
        # for a single date/time
        return pd.to_timedelta(time) + pd.to_datetime(date, utc=True)

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

def change_extension(path, extension):
    p, e = os.path.splitext(path)
    return '{}.{}'.format(p, extension)

def read_json_file(json_file, check_exists=True, encoding='utf-8'):
    json_file = change_extension(json_file, 'json')
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding=encoding) as fin:
            return json.load(fin) 
    if check_exists:
        raise KeyError('cannot find JSON file {}'.format(json_file))
    return {}

# os utilities

def safe_makedirs(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        return

# pandas utilities

def delete_row(df, ix):
    df = df.copy()
    return df[df.index != ix]

def update_cell(df, ix, col, new_value):
    df = df.copy()
    df.at[ix, col] = new_value
    return df

def interpolate_timeseries(data, new_timebase):
    """data should be time-indexed, new_timebase should be a series-like list of datetimes.
    both must be sorted"""
    idx = data.index.union(new_timebase)
    interped = data.reindex(idx).interpolate().reindex(new_timebase)
    return interped

# subclass of DataFrame that carries a property called "metadata"
# which is intended to be a dict of k/v pairs

class DataTable(pd.DataFrame):
    """DataFrame with a metadata property"""
    # note that it is a coincidence that when subclassing a dataframe
    # the extra properties are stored in a variable called _metadata.
    # here I'm just adding one property which is called "metadata"
    # but it could have been called anything
    _metadata = ['metadata']
    
    @property
    def _constructor(self):
        return DataTable

def data_table(df, **metadata):
    """convenience function for transforming a vanilla DataFrame into
    one that contains metadata k/v pairs"""
    dt = DataTable(df)
    try:
        # is this already a datatable with metadata?
        existing_md = dt.metadata
        dt.metadata = existing_md.update(metadata)
    except AttributeError:
        dt.metadata = metadata
    return dt

def metadata_file(product_path):
    product_dir = os.path.dirname(product_path)
    product_name = os.path.basename(product_path)
    p, _ = os.path.splitext(product_name)
    return os.path.join(product_dir, '{}_metadata.json'.format(p))

def read_metadata_file(product_path, check_exists=True):
    metadata_path = metadata_file(product_path)
    return read_json_file(p_path, check_exists=check_exists)

def write_dt(dt, product_path):
    """writes a datatable as csv with sidecar metadata file"""
    product_path = change_extension(product_path, 'csv')
    dt.to_csv(product_path, index=None, encoding='utf-8')
    md_file = metadata_file(product_path)
    md = dt.metadata
    with open(md_file, 'w', encoding='utf-8') as fout:
        json.dump(md, fout)
