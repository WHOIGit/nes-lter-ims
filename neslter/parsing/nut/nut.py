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

def merge_nut_bottles(sample_log_path, nut_path, bottle_summary, cruise):
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

    # drop rows (picked up in btl_sum.merge right) with casts that were not in btl_sum
    nut_profile.dropna(subset=['date'], inplace=True)
    if cruise.lower() in JP_STUDENT_CRUISES:
        nut_profile['project_id'] = 'JP'
    else:
        nut_profile['project_id'] = np.where(nut_profile['alternate_sample_id'].isna(), 'LTER', 'OOI')
    return nut_profile
