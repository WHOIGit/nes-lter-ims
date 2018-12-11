import re
from io import StringIO
import os
from glob import glob

import pandas as pd

from neslter.parsing.ctd.hdr import HdrFile
from neslter.parsing.utils import clean_column_names, doy_to_datetime

def compile_underway(csv_dir, resolution=60):
    """compile daily underway files"""
    assert resolution in [1, 60] # not aware of any other resolutions
    dfs = []
    for fn in os.listdir(csv_dir):
        # files have names like Data60Sec_Daily_20180204-000000.csv
        if not re.match(r'Data{}Sec_Daily_\d+-\d+\.csv'.format(resolution), fn):
            continue
        path = os.path.join(csv_dir, fn)
        dfs.append(pd.read_csv(path, comment='#'))
    df = clean_column_names(pd.concat(dfs))
    df.index = pd.to_datetime(df['datetime_iso8601'])
    return df

def read_cnv(path, year):
    """read a .cnv file containing underway data.
    deprecated, use compile_underway instead"""
    assert os.path.exists(path)
    # skip header lines
    with open(path) as fin:
        lines = [l for l in fin.readlines() if not re.match('^[#*]', l)]
    txt = ''.join(lines)
    # read the space-delimited data
    # FIXME might actually be fixed-width
    df = pd.read_csv(StringIO(txt), delimiter=r'\s+', header=None)
    # read header data to get column names
    hdr = HdrFile(path, parse_filename=False)
    df.columns = hdr.names
    df = clean_column_names(df)
    # convert dates from decimal day of year to proper datetimes
    df['date'] = doy_to_datetime(df.timej, year)
    return df