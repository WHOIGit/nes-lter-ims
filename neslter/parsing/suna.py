from io import StringIO

import pandas as pd
import numpy as np

from neslter.parsing.utils import clean_column_names

def parse_suna_cal(cal_file_path):
    with open(cal_file_path) as fin:
        data = fin.readlines()

    for l in data:
        if l.startswith('H,T_CAL '):
            t_cal = float(l[8:])

    data = [l for l in data if not l.startswith('H')]

    df = pd.read_csv(StringIO(''.join(data)), header=None)
    df.columns = ['ignore','wavelength','no3','swa','tswa','reference']
    df.pop('ignore')
    df.pop('tswa')

    return t_cal, df.wavelength, df.no3, df.swa, df.reference

def parse_suna_data(data_file_path):
    df = pd.read_csv(data_file_path, skiprows=3, comment='#')
    df = clean_column_names(df)

    # ignore dark frames
    df = df[~(df.dark_avg == 0)] # ignore dark frames

    # parse timestamps
    df.date_utc_00_00 = df.date_utc_00_00.astype(str)
    timestamp = pd.to_datetime(df.date_utc_00_00, format='%Y%j', utc=True) + \
        pd.to_timedelta(df.time_utc_00_00, unit='h')

    # format parameters for ts_corrected_nitrate

    N = len(df)

    dark_value = df.dark_avg # simple rename

    # dummy frame type indicating that we've skipped all dark frames
    frame_type = np.array(list('SLB' for _ in range(N)))

    data_df_columns = [col for col in df.columns if col.startswith('uv')]
    data_df = df[data_df_columns]
    data_in = data_df.to_numpy()

    return timestamp, dark_value, frame_type, data_in