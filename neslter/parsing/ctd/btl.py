import math
from glob import glob
import os
import pandas as pd 

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
    assert justification in ['left', 'right', 'center']
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
    def __init__(self, path, parse=True):
        super(BtlFile, self).__init__(path, parse)
        self._df = None
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
        df[DATE_COL] = pd.to_datetime(df[DATE_COL])

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

def find_btl_file(dir, cruise, cast):
    for path in glob(os.path.join(dir, '*.btl')):
        try:
            cr, ca = pathname2cruise_cast(path)
        except ValueError:
            continue
        if cr.lower() == cruise.lower() and int(ca) == int(cast):
            return BtlFile(path)

def parse_btl(in_path, add_depth=True):
    btl = BtlFile(in_path)
    df = btl.to_dataframe()
    # add depth column if necessary
    if add_depth and DEPTH_COL not in df.columns and PRESSURE_COL in df.columns:
        df[DEPTH_COL] = btl.depths().values
    clean_column_names(df)
    return df