import os
from glob import glob

import numpy as np
import pandas as pd

from ..utils import clean_column_names, dropna_except, format_dataframe, wide_to_long
from ..cruises import JP_STUDENT_CRUISES
from neslter.parsing.files import Resolver
from neslter.parsing.ctd.common import pathname2cruise_cast

from neslter.parsing.files import DataNotFound

RAW_COLS = ['Nutrient \nNumber', 'Cruise', 'Cast', 'LTER \nSample ID', 'Nitrate + Nitrite', 'Ammonium',
       'Phosphate', 'Silicate', 'Comments']

NUT_COLS = ['nitrate_nitrite', 'ammonium', 'phosphate', 'silicate']

def parse_nut(nut_xl_path):
    df = pd.read_excel(nut_xl_path, skiprows=[0,1])
    if set(df.columns) != set(RAW_COLS):
        raise ValueError('Nut spreadsheet does not contain expected columns')
    df = clean_column_names(df)
    #df = dropna_except(df, ['comments']) # is this necessary?
    df['comments'] = df['comments'].fillna('')
    # deal with below-detection-limit values
    # for the nut cols, add {}_bdl col with the
    # detection limit value, for all below-detection-limit
    # values. in the value column put a zero
    for col in NUT_COLS:
        bdl = []
        new_values = []
        for v in df[col].values:
            if str(v).startswith('<'): # below detection limit
                detection_limit = float(str(v)[1:])
                bdl.append(detection_limit)
                new_values.append(0)
            else:
                bdl.append(np.nan)
                new_values.append(v)
        bdl_col = '{}_bdl'.format(col)
        df[bdl_col] = bdl
        df[col] = new_values
    #
    df['lter_sample_id'] = df['nutrient_number'].str.replace('NL_','')
    return df

def format_nut(df):
    prec = { c: 3 for c in NUT_COLS }
    return format_dataframe(df, precision=prec)

def apply_flags(df):

# Flagging scheme based on IODE flag
# 1 = good
# 2 = not reviewed
# 3 = questionable
# 4 = bad (always throw out)

# Detection Limit diff for each nutrient
# nitrate_nitrite = 0.04
# ammonium = 0.015
# phosphate = 0.009
# silicate = 0.030

# Set all OOI ammonium flags to 3, all other OOI flags to 2

    DL_dict = {
        'nitrate_nitrite': 0.04,
        'ammonium': 0.01,
        'phosphate': 0.009,
        'silicate': 0.03
    }
    flag_dict = {
        'nitrate_nitrite': 'flag_nitrate_nitrite',
        'ammonium': 'flag_ammonium',
        'phosphate': 'flag_phosphate',
        'silicate': 'flag_silicate'
    }

    diff_dict = {
        'nitrate_nitrite': 8.5,
        'ammonium': 99,         # 99 represents no processing
        'phosphate': 99,
        'silicate': 99
    }

# First step of flagging
    df['time'] = pd.to_datetime(df['date'], format='%Y-%m-%d %H:%M:%S')
    df['time_numeric'] = df['time'].map(lambda x: x.toordinal() + x.hour / 24 + x.minute / 1440 + x.second / 86400)

    # Adjust values below detection limits
    for param, DL in DL_dict.items():
        df[param] = pd.to_numeric(df[param], errors='coerce')  #ar61b
        df[param] = df[param].clip(lower=DL)

    # Add flag columns with default values
    for param in DL_dict.keys():
        df[flag_dict[param]] = 1

    # Calculate and apply ratios/differences
    for idx, row in df.iterrows():
        close_rows = df[
            (np.abs((df['time'] - row['time']).dt.total_seconds()) < 60) &
            (np.abs(df['depth'] - row['depth']) < 3) &
            (df.index != idx) &
            (row['project_id'] != 'OOI') &
            (df['project_id'] != 'OOI')
        ]
        for param in DL_dict.keys():
            if not close_rows.empty:
                mean_value = (close_rows[param].mean() + row[param]) / 2
                ratio = 100 * (row[param] - mean_value) / mean_value           
                if len(close_rows) >= 2: 
                   # Compare sample value against mean of the other rows
                   if abs(close_rows[param].mean() - row[param]) > diff_dict[param]:
                       df.at[idx, flag_dict[param]] = 4
                   else:
                       # Apply different thresholds for ammonium
                       if param == "ammonium":
                           if abs(ratio) > 50:
                               df.at[idx, flag_dict[param]] = 4
                           elif abs(ratio) > 20:
                               df.at[idx, flag_dict[param]] = 3
                       else:
                           if abs(ratio) > 40:
                               df.at[idx, flag_dict[param]] = 4
                           elif abs(ratio) > 15:
                               df.at[idx, flag_dict[param]] = 3
                else:
                    # Apply different thresholds for ammonium
                    if param == "ammonium":
                        if abs(ratio) > 50:
                            df.at[idx, flag_dict[param]] = 4
                        elif abs(ratio) > 20:
                            df.at[idx, flag_dict[param]] = 3
                    else:
                        if abs(ratio) > 40:
                            df.at[idx, flag_dict[param]] = 4
                        elif abs(ratio) > 15:
                            df.at[idx, flag_dict[param]] = 3
            else:
                # set single row value to not reviewed
                if (param == 'ammonium') & (df.at[idx, 'project_id'] == 'OOI'):
                    df.at[idx, flag_dict[param]] = 3
                else:
                    df.at[idx, flag_dict[param]] = 2

# 1st step of lter nut flagging doesn't work well for low concentrations. 
# this 2nd step changes flag=4(bad) to flag=3(caution) to be more lenient. 
# next step is manual inspection of all flagged data
# do not want to be too lenient and change flags to 1(good) because good will not be manually inspected

# 2nd step = if both replicates are less than DetectionLimit * 10, then change from bad to caution
# Detection Limit (DL) is nutrient specific

    # Refine flags for low concentrations
    for param, DL in DL_dict.items():
        flag_col = flag_dict[param]
        for idx, row in df.iterrows():
            if row[flag_col] == 4:
                close_rows = df[
                    (np.abs(df['time_numeric'] - row['time_numeric']) < 1 / (24 * 60)) &
                    (np.abs(df['depth'] - row['depth']) < 3) 
                ]
                if len(close_rows) > 1 and (close_rows[param] < DL * 10).sum() > 1 and row[param] < DL * 10:
                    df.at[idx, flag_col] = 3

    # Drop helper columns
    df.drop(columns=['time', 'time_numeric'], inplace=True)
    return df


def merge_nut_bottles(sample_log_path, nut_path, bottle_summary, bottles, cruise):
    if not os.path.exists(sample_log_path):
        raise DataNotFound('Sample log path not found at {}'.format(sample_log_path))
    if not os.path.exists(nut_path):
        raise DataNotFound('Nutrient path not found at {}'.format(nut_path))
    # parse the LTER sample log
    raw = pd.read_excel(sample_log_path, na_values='-', dtype={
        'Nut a': str,
        'Nut b': str,
        'Niskin #': str
    })
    df = clean_column_names(raw, {
        'Date \n(UTC)': 'date',
        'Start Time (UTC)': 'time',
        'Niskin #': 'niskin',
        'Niskin\nTarget\nDepth': 'depth',
    })
    # for ar24 some niskin numbers are given as a list in the sample log (e.g., "4,5,6")
    # so pick the first one for now, proposed solution is to average the CTD bottle data
    df['niskin'] = df['niskin'].fillna('0').str.replace(',.*','',regex=True).astype(int)
    df['Comments'] = df.comments.fillna('')
    # drop rows without an a replicate
    df = df[['cruise','cast','niskin','nut_a','nut_b', 'ooi_nut_id']].dropna(subset=['nut_a'])
    df = df[df['cruise'] == cruise.upper()]
    # make replicates long instead of wide
    sample_ids = wide_to_long(df, [['nut_a'],['nut_b']], ['sample_id'], 'replicate', ['a','b'])
    # merge with bottle summary
    btl_sum = bottle_summary
    sample_ids.cast = sample_ids.cast.astype(str)
    btl_sum.cast = btl_sum.cast.astype(str).str.lstrip("0")  #remove leading 0s for merge
    sample_ids.niskin = sample_ids.niskin.astype(int)
    btl_sum.niskin = btl_sum.niskin.astype(int)
    # include sample_ids cast rows when cast missing from btl_sum
    merged = btl_sum.merge(sample_ids, on=['cruise','cast','niskin'], how='right')
    # merge nutrient data
    nit = parse_nut(nut_path)[['lter_sample_id','nitrate_nitrite','ammonium','phosphate','silicate']]
    nit['sample_id'] = nit.pop('lter_sample_id').astype(str)
    nut_profile = merged.merge(nit, on='sample_id')
    nut_profile['date'] = pd.to_datetime(nut_profile['date'], utc=True)
    # sort alphanumeric casts in numeric order (not alpha order) such that 2 preceeds 12
    nut_profile['cast'] = pd.to_numeric(nut_profile['cast'])
    nut_profile = nut_profile.sort_values(['cast','niskin','replicate'])
    nut_profile['cast'] = nut_profile['cast'].astype(str)
    nut_profile['alternate_sample_id'] = nut_profile.pop('ooi_nut_id')

    # set date, lat, lon, depth to NaN when there is no bottle file for the cast
    btl_dir = Resolver().raw_directory('ctd', cruise)
    for file in sorted(glob(os.path.join(btl_dir, '*.asc'))):
        if cruise == 'en627':
            file = file.replace("_u", "")
        btl_file = file[:-3] + 'btl'
        if not os.path.exists(btl_file):
            _, cast = pathname2cruise_cast(btl_file)
            if cast is None:
                 continue
            cast = cast.lstrip('0')
            nut_profile.loc[nut_profile['cast'] == cast, 'date'] = ''
            nut_profile.loc[nut_profile['cast'] == cast, 'latitude'] = 'NaN'
            nut_profile.loc[nut_profile['cast'] == cast, 'longitude'] = 'NaN'
            nut_profile.loc[nut_profile['cast'] == cast, 'depth'] = 'NaN'

    # merge temperature and salinity from bottle data
    bottles.cast = bottles.cast.astype(str).str.lstrip("0")
    nut_profile = nut_profile.merge(
        bottles[['cruise', 'cast', 'niskin', 't090c', 't190c', 'sal00', 'sal11']], 
        on=['cruise', 'cast', 'niskin'], 
        how='right'
    )

    # drop rows (picked up in btl_sum.merge right) with casts that were not in btl_sum
    nut_profile.dropna(subset=['date'], inplace=True)
    if cruise.lower() in JP_STUDENT_CRUISES:
        nut_profile['project_id'] = 'JP'
    else:
        nut_profile['project_id'] = np.where(nut_profile['alternate_sample_id'].isna(), 'LTER', 'OOI')

    # calculate and apply quality flags
    nut_profile = apply_flags(nut_profile)

    return nut_profile
