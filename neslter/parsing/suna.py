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

    return t_cal, df.wavelength, df.no3, df.swa, df.reference

def parse_suna_csv(data_file_path):
    df = pd.read_csv(data_file_path, skiprows=3, comment='#')
    df = clean_column_names(df)

    # parse timestamps
    df.date_utc_00_00 = df.date_utc_00_00.astype(str)
    date_formats = ['%Y%j', None]
    for date_format in date_formats:
        try:
            timestamp = pd.to_datetime(df.date_utc_00_00, format=date_format, infer_datetime_format=True, utc=True) + \
                pd.to_timedelta(df.time_utc_00_00, unit='h')
            break
        except ValueError:
            pass

    df['timestamp'] = timestamp

    return df

ENG_COLUMNS = ['t_int', 't_spec', 't_lamp', 'lamp_time', 'humidity', 'volt_main', 'volt_12', 'volt_5', 'current']

def parse_suna_data(data_file_path):
    df = parse_suna_csv(data_file_path)


    # ignore dark frames
    df = df[~(df.dark_avg == 0)] # ignore dark frames

    timestamp = df.timestamp
    raw_nitrate = df.nitrate_um

    # format parameters for ts_corrected_nitrate

    N = len(df)

    dark_value = df.dark_avg # simple rename

    # dummy frame type indicating that we've skipped all dark frames
    frame_type = np.array(list('SLB' for _ in range(N)))

    data_df_columns = [col for col in df.columns if col.startswith('uv')]
    data_df = df[data_df_columns]
    data_in = data_df.to_numpy()

    # engineering data
    eng = df[ENG_COLUMNS]

    return timestamp, dark_value, frame_type, data_in, raw_nitrate, eng
