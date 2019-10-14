import os

import pandas as pd
import numpy as np

from neslter.parsing.ctd.hdr import HdrFile
from neslter.parsing.ctd.asc import parse_asc
from neslter.parsing.nut import parse_nut

from .ts_correction import ts_corrected_nitrate

from neslter.parsing.suna import parse_suna_data, parse_suna_cal
from neslter.parsing.utils import interpolate_timeseries, clean_column_names, wide_to_long

"""
perform an analysis on en627 data to estimate offset between sampled nitrate data
and t/s corrected SUNA nitrate data from casts.

The required information:
* time-indexed CTD temperature / salinity data (see prepare_cast_data)
* SUNA calibration and data
* Sosik lab sample log
* Sosik lab nutrient data
"""

def prepare_cast_data(asc_path_or_cast_data, hdr_path):
    assert os.path.exists(hdr_path)
    try:
        _ = asc_path_or_cast_data.columns
        cast = asc_path_or_cast_data
    except AttributeError:
        assert os.path.exists(asc_path_or_cast_data)
        cast = parse_asc(asc_path_or_cast_data)
    assert 'times' in cast.columns
    hf = HdrFile(hdr_path)
    times = hf.time + pd.to_timedelta(cast.times, unit='s')
    cast.index = times
    return cast

def suna2nitrate(cal_file_path, data_file_path, cast_data, t_var='t090c', s_var='sal00', d_var='depsm'):
    assert os.path.exists(cal_file_path)
    assert os.path.exists(data_file_path)
    assert d_var in cast_data.columns
    assert t_var in cast_data.columns
    assert s_var in cast_data.columns
    # cast data must be indexed by time, see prepare_cast_data
    t_cal, wavelength, no3, swa, reference = parse_suna_cal(cal_file_path)
    suna_ts, dark_value, frame_type, data_in, raw_nitrate, eng = parse_suna_data(data_file_path)
    tsal = cast_data[[t_var, s_var, d_var]]
    tsal_interp = interpolate_timeseries(tsal, suna_ts).fillna(0)
    degc = tsal_interp[t_var]
    psu = tsal_interp[s_var]
    nitrate = ts_corrected_nitrate(t_cal, wavelength, no3, swa, reference, dark_value, degc, psu, data_in, frame_type)
    out = pd.DataFrame({
        'nitrate': nitrate,
        'raw_nitrate': raw_nitrate.values, # FIXME is this correct?
        'temperature': degc,
        'salinity': psu
    }, index=suna_ts)
    for ec in eng.columns:
        out[ec] = eng[ec].values
    return out

def nutrient_profile(sample_log_path, nut_path, cast_number, cruise='en627'):
    assert os.path.exists(sample_log_path)
    assert os.path.exists(nut_path)
    raw = pd.read_excel(sample_log_path, na_values='-', dtype={
        'Nut a': str,
        'Nut b': str
    })
    df = clean_column_names(raw, {
        'Date \n(UTC)': 'date',
        'Start Time (UTC)': 'time',
        'Niskin #': 'niskin',
        'Niskin\nTarget\nDepth': 'depth',
    })
    df['Comments'] = df.comments.fillna('')
    df = df[['cruise','cast','niskin','nut_a','nut_b']].dropna(subset=['nut_a'])
    df = df[df['cruise'] == cruise.upper()]
    sample_ids = wide_to_long(df, [['nut_a'],['nut_b']], ['sample_id'], 'replicate', ['a','b'])
    # for en627 we can use the API to fetch bottle summary data
    btl_sum = pd.read_csv('https://nes-lter-data.whoi.edu/api/ctd/{}/bottle_summary.csv'.format(cruise))
    merged = btl_sum.merge(sample_ids, on=['cruise','cast','niskin'])
    nit = parse_nut(nut_path)[['lter_sample_id','nitrate_nitrite','ammonium','phosphate','silicate']]
    nit['sample_id'] = nit.pop('lter_sample_id').astype(str)
    nut_profile = merged.merge(nit, on='sample_id')
    nut_profile.index = pd.to_datetime(nut_profile['date'], utc=True)
    return nut_profile[nut_profile.cast == cast_number]

def compute_nut_vs_suna(cast_data, nitrate, nut_profile, d_var='depsm'):
    cast_start = cast_data.index[0]
    # assume the upcast starts at max depth, reasonable for this case
    upcast_start = cast_data[d_var].idxmax()
    cast_end = cast_data.index[-1]
    cast_nit = nitrate[upcast_start:cast_end]
    nit_df = interpolate_timeseries(cast_nit, nut_profile.index.unique())
    nitp = nit_df.nitrate
    nits = nit_df.salinity
    nitt = nit_df.temperature
    rep_a = nut_profile[nut_profile['replicate'] == 'a']
    rep_b = nut_profile[nut_profile['replicate'] == 'b']
    nutp_a = rep_a['nitrate_nitrite']
    nutp_b = rep_b['nitrate_nitrite']   
    dep_a = rep_a['depth']
    dep_b = rep_b['depth']
    nuta_vs_suna = pd.DataFrame({'nut': nutp_a, 'suna': nitp, 'depth': dep_a, 'temperature': nitt, 'salinity': nits })
    nutb_vs_suna = pd.DataFrame({'nut': nutp_b, 'suna': nitp, 'depth': dep_b, 'temperature': nitt, 'salinity': nits })
    nut_vs_suna = pd.concat([nuta_vs_suna, nutb_vs_suna])
    nut_vs_suna['date'] = nut_vs_suna.index
    nut_vs_suna.index = range(len(nut_vs_suna))
    return nut_vs_suna

def estimate_offset(cast_data, nitrate, nut_profile, d_var='depsm'):
    cast_start = cast_data.index[0]
    # assume the upcast starts at max depth, reasonable for this case
    upcast_start = cast_data[d_var].idxmax()
    cast_end = cast_data.index[-1]
    cast_nit = nitrate[upcast_start:cast_end]
    nutp_a = nut_profile[nut_profile['replicate'] == 'a']['nitrate_nitrite']
    nutp_b = nut_profile[nut_profile['replicate'] == 'b']['nitrate_nitrite']
    metric = []
    offsets = []
    for offset in np.arange(1,5,0.01):
        nitp = interpolate_timeseries(cast_nit + offset, nut_profile.index.unique())
        offsets.append(offset)
        metric.append((nutp_a-nitp).sum())
    best_offset = pd.Series(metric, index=offsets).abs().idxmin()
    return best_offset
