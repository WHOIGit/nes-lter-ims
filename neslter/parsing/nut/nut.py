import os

import numpy as np
import pandas as pd

from ..utils import clean_column_names, dropna_except, format_dataframe, wide_to_long
from ..cruises import JP_STUDENT_CRUISES

RAW_COLS = ['Nutrient \nNumber', 'Cruise', 'Cast', 'LTER \nSample ID', 'Nitrate + Nitrite', 'Ammonium',
       'Phosphate', 'Silicate', 'Comments']

NUT_COLS = ['nitrate_nitrite', 'ammonium', 'phosphate', 'silicate']

def parse_nut(nut_xl_path):
    df = pd.read_excel(nut_xl_path, skiprows=[0,1])
    assert set(df.columns) == set(RAW_COLS), 'nut spreadsheet does not contain expected columns'
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

def fix_ooi_nut_replicates(df):
    # specifically deal with case where OOI took replicates
    # and the OOI nut ID column looks like '6-1/6-2'
    rep_a = df[df.replicate == 'a']
    rep_b = df[df.replicate == 'b']
    rep_a.loc[:,'ooi_nut_id'].str.replace(r'/.*','')
    rep_b.loc[:,'ooi_nut_id'].str.replace(r'/.*','')
    return pd.concat([rep_a, rep_b])

def merge_nut_bottles(sample_log_path, nut_path, bottle_summary, cruise):
    assert os.path.exists(sample_log_path)
    assert os.path.exists(nut_path)
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
    btl_sum.cast = btl_sum.cast.astype(str).str.strip("0")  #remove leading 0 for merge
    sample_ids.niskin = sample_ids.niskin.astype(int)
    btl_sum.niskin = btl_sum.niskin.astype(int)
    merged = btl_sum.merge(sample_ids, on=['cruise','cast','niskin'])
    # sort alphanumeric casts in numeric order (not alpa order) such that 2 preceeds 12
    a = merged.index.to_series().astype(int).sort_values()
    merged = merged.reindex(index=a.index)
    # merge nutrient data
    nit = parse_nut(nut_path)[['lter_sample_id','nitrate_nitrite','ammonium','phosphate','silicate']]
    nit['sample_id'] = nit.pop('lter_sample_id').astype(str)
    nut_profile = merged.merge(nit, on='sample_id')
    nut_profile['date'] = pd.to_datetime(nut_profile['date'], utc=True)
    nut_profile = fix_ooi_nut_replicates(nut_profile)
    nut_profile = nut_profile.sort_values(['cast','niskin','replicate'])
    nut_profile['alternate_sample_id'] = nut_profile.pop('ooi_nut_id')
    if cruise.lower() in JP_STUDENT_CRUISES:
        nut_profile['project_id'] = 'JP'
    else:
        nut_profile['project_id'] = np.where(nut_profile['alternate_sample_id'].isna(), 'LTER', 'OOI')
    return nut_profile
