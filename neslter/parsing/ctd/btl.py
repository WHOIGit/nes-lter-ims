import math
from glob import glob
import os
import warnings
import numpy as np
import pandas as pd

from neslter.parsing.files import DataNotFound 

from .common import CtdTextParser, pathname2cruise_cast
from ..utils import clean_column_names

# column names

BOTTLE_COL = 'Bottle'
DATE_COL = 'Date'
# date column is the second column (index 1)
DATE_COL_IX = 1

PRESSURE_COL = 'PrDM'
DEPTH_COL = 'DepSM'

LAT_COL = 'Latitude'
LON_COL = 'Longitude'

CRUISE_COL = 'Cruise'
CAST_COL = 'Cast'

def _col_values(line, col_widths, justification='right'):
    """read fixed-width column values"""
    if justification not in ['left', 'right', 'center']:
        raise ValueError('Justification not left, right, or center')
    vals = []
    i = 0

    for w in col_widths:
        start = i
        end = i + w
        raw_val = line[start:end]
        # handle justification
        if justification == 'right':
            val = raw_val.lstrip()
        elif justification == 'left':
            val = raw_val.rstrip()
        elif justification == 'center':
            val = raw_val.lstrip().rstrip()
        vals.append(val)
        i += w

    return vals

def p_to_z(p, latitude):
    """convert pressure to depth in seawater.
    p = pressure in dbars
    latitude"""

    # use the Seabird calculation
    # from http://www.seabird.com/document/an69-conversion-pressure-depth

    x = math.pow(math.sin(latitude / 57.29578),2)
    g = 9.780318 * ( 1.0  + (5.2788e-3 + 2.36e-5 * x) * x ) + 1.092e-6 * p
    
    depth_m_sw = ((((-1.82e-15 * p + 2.279e-10) * p - 2.2512e-5) * p + 9.72659) * p) / g
    
    return depth_m_sw

class BtlFile(CtdTextParser):
    def __init__(self, path, **kw):
        self._df = None
        super(BtlFile, self).__init__(path, **kw)
    def to_dataframe(self):
        if self._df is not None:
            return self._df

        # read lines of file, skipping headers
        lines = []

        for l in self._lines:
            if l.startswith('#') or l.startswith('*'):
                continue
            lines.append(l)

        # column headers are fixed width at 11 characters per column,
        # except the first two
        h1_width = 10
        h2_width = 12

        n_cols = ((len(lines[0]) - (h1_width + h2_width)) // 11) + 2

        header_col_widths = [h1_width,h2_width] + [11] * (n_cols - 2)

        # the first line is the first line of column headers; skip the second
        col_headers = _col_values(lines[0], header_col_widths)

        # discard the header lines, the rest are data lines
        lines = lines[2:]

        # data lines are in groups of 4 (if min/max is written to the file)
        # or in groups of 2

        n_lines_per_sample = 2

        for line in lines:
            if line.endswith('(min)'): # min/max are present
                n_lines_per_sample = 4
                break

        # average values are every 2 or 4 lines
        avg_lines = lines[::n_lines_per_sample]
        # the lines with the time (and stddev values) are the ones immediately
        # following the average value lines
        time_lines = lines[1::n_lines_per_sample]

        # value columns are fixed width 11 characters per col except the first two
        bottle_column_width = 7 # bottle number column
        datetime_column_width = 15 # date/time column

        value_col_widths = [11] * (n_cols - 2)
        col_widths = [bottle_column_width, datetime_column_width] + value_col_widths

        # now assemble the rows of the dataframe
        rows = []

        for al, tl in zip(avg_lines, time_lines):
            cvs = _col_values(al, col_widths)
            # date/time is split across two rows
            time = _col_values(tl, col_widths)[DATE_COL_IX]
            cvs[DATE_COL_IX] = '{} {}'.format(cvs[DATE_COL_IX], time)
            rows.append(cvs)

        df = pd.DataFrame(rows, columns=col_headers)

        # convert df columns to reasonable types
        df[BOTTLE_COL] = df[BOTTLE_COL].astype(int)
        df[DATE_COL] = pd.to_datetime(df[DATE_COL], utc=True)

        for c in df.columns[2:]:
            df[c] = df[c].astype(float)

        # add cruise / cast
        df[CRUISE_COL] = self.cruise
        df[CAST_COL] = self.cast

        # move those columns to the front
        cols = df.columns.tolist()
        cols = cols[-2:] + cols[:-2]
        df = df[cols]

        # all done

        self._df = df

        return df


    def _col(self, col_name):
        df = self.to_dataframe()
        s = df[col_name]
        s.index = df[BOTTLE_COL]
        return s

    def _col_or_constant(self, col_name, constant):
        df = self.to_dataframe()
        if col_name not in df.columns:
            return pd.Series(constant, index=df[BOTTLE_COL])
        else:
            return self._col(col_name)

    def times(self):
        return self._col(DATE_COL)

    def lats(self):
        return self._col_or_constant(LAT_COL, self.lat)

    def lons(self):
        return self._col_or_constant(LON_COL, self.lon)

    def depths(self):
        df = self.to_dataframe()
        if DEPTH_COL in df.columns:
            return self._col(DEPTH_COL)
        elif PRESSURE_COL in df.columns:
            ps = [p_to_z(p, self.lat) for p in df[PRESSURE_COL]]
            s = pd.Series(ps, index=df[BOTTLE_COL])
            return s
        else:
            raise KeyError('no source of depth information found')

def find_btl_files(dir):
    for path in glob(os.path.join(dir, '*.btl')):
        yield path

def find_btl_file(dir, cruise, cast):
    for path in find_btl_files(dir):
        cr, ca = pathname2cruise_cast(path, skip_bad_filenames=True)
        if cr is None:
            continue
        if cr.lower() == cruise.lower() and int(ca) == int(cast):
            return BtlFile(path)

def parse_btl(in_path, add_depth=True, add_lat_lon=True):
    btl = BtlFile(in_path)
    df = btl.to_dataframe()
    # add depth column if necessary
    if add_depth and DEPTH_COL not in df.columns and PRESSURE_COL in df.columns:
        df[DEPTH_COL] = btl.depths().values
    # add lat/lon if necessary
    if add_lat_lon and LAT_COL not in df.columns and LON_COL not in df.columns:
        df[LAT_COL] = btl.lats().values
        df[LON_COL] = btl.lons().values
    df = clean_column_names(df, {
        'Bottle': 'niskin'
        })
    df = df.astype({ 'niskin': int })
    return df

def compile_btl_files(in_dir, add_depth=True, add_lat_lon=True, summary=False):
    """convert a set of bottle files to a single dataframe"""
    dfs = []
    paths = find_btl_files(in_dir)
    for path in paths:
        cr, ca = pathname2cruise_cast(path, skip_bad_filenames=True)
        if cr is None:
            warnings.warn('cannot parse cruise and cast from "{}"'.format(path))
            continue
        df = parse_btl(path, add_depth=add_depth, add_lat_lon=add_lat_lon)
        # remove duplicate columns if any
        df = df.loc[:,~df.columns.duplicated()].copy()
        dfs.append(df)
    if not dfs:
        raise DataNotFound('no bottle files found in {}'.format(in_dir))
    compiled_df = pd.concat(dfs, sort=False)
    compiled_df = compiled_df.sort_values(['cast','niskin'])
    compiled_df.reset_index()
    if summary:
        return summarize_compiled_btl_files(compiled_df)
    else:
        return compiled_df

def summarize_compiled_btl_files(compiled_df):
    """extract just the following columns from a dataframe produced by
    compile_btl_files:
    - cruise/cast/niskin
    - date
    - lat/lon/depth
    compiled btl dataframe must include a 'depsm' column for depth"""
    def sort_cruise_cast_niskin(df_with_cast_niskin):
        # sort on those columns even though they're strings
        df = df_with_cast_niskin.copy()
        # the strings are just integers, so we can cast
        df['niskin'] = df['niskin'].astype(int)
        df = df.sort_values(['cruise','cast','niskin'])
        df['cast'] = df['cast'].astype(str)
        df['niskin'] = df['niskin'].astype(str)
        return df

    # subset the columns and do some renaming
    btl = compiled_df.loc[:,['cruise','cast','niskin','date','latitude','longitude','depsm']]
    btl = btl.rename(columns={'depsm':'depth'})
    # convert lat/lon to floats
    btl['latitude'] = btl['latitude'].astype(float)
    btl['longitude'] = btl['longitude'].astype(float)
    # convert numeric cs-c1s/m to NaN if blank
    if 'c2_c1s_m' in btl.columns:
        btl['c2_c1s_m'].replace('', np.nan, inplace=True)
    # sort by cruise, cast, niskin
    btl = sort_cruise_cast_niskin(btl)
    return btl
