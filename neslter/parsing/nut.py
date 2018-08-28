import os

from scipy.io import loadmat
import pandas as pd

def parse_nut(in_mat_file):
    mat = loadmat(in_mat_file, squeeze_me=True)
    # construct dataframe
    # column renaming map
    COL_MAP = {
      'Event_Number': 'event_number',
      'Event_Number_Niskin': 'event_number_niskin',
      'Latitude': 'latitude',
      'Longitude': 'longitude',
      'Depth': 'depth',
      'Nut_a_uM NO2- + NO3-': 'ntra_a',
      'Nut_b_uM NO2- + NO3-': 'ntra_b',
      'Nut_c_uM NO2- + NO3-': 'ntra_c',
      'Nut_a_uM NH4+': 'amon_a',
      'Nut_b_uM NH4+': 'amon_b',
      'Nut_c_uM NH4+': 'amon_c',
      'Nut_a_uM SiO2-': 'slca_a',
      'Nut_b_uM SiO2-': 'slca_b',
      'Nut_c_uM SiO2-': 'slca_c',
      'Nut_a_uM PO43-': 'phos_a',
      'Nut_b_uM PO43-': 'phos_b',
      'Nut_c_uM PO43-': 'phos_c',
    }
    # now parse mat file
    cols = mat['header_nut']
    expected_columns = set(COL_MAP.keys()).union(set(['Start_Date','Start_Time_UTC']))
    assert set(cols) == expected_columns, 'nutrient .mat file does not contain expected headers'
    d = {}
    for i, col in enumerate(cols):
        d[col] = pd.Series(list(mat['MVCO_nut_reps'][:,i]))
    df = pd.DataFrame(d, columns=cols)
    # compute datetimes from start date and incorrect start time cols
    dt = []
    for d, t in zip(df['Start_Date'], df['Start_Time_UTC']):
        dt.append(pd.to_datetime('{}T{}Z'.format(d[:10],t[11:])))
    dt = pd.Series(dt)
    # add to dataframe
    df['time'] = dt
    del df['Start_Date']
    del df['Start_Time_UTC']
    # rename columns
    df = df.rename(columns=COL_MAP)
    data_cols = []
    for var in ['ntra', 'slca', 'phos', 'amon']:
        for replicate in ['a', 'b', 'c']:
            colname = '{}_{}'.format(var, replicate)
            data_cols.append(colname)
    cols = ['time', 'latitude', 'longitude', 'depth', 'event_number'] + data_cols
    # ^ FIXME include niskin?
    df = df[cols]
    # chop off everything before april 2006
    df = df[df['time'] >= '2006-04-01']
    return df