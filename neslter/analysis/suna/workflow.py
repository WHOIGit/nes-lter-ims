import os
import re

import pandas as pd

from neslter.parsing.suna import parse_suna_data, parse_suna_csv, ENG_COLUMNS
from neslter.parsing.ctd.asc import list_casts, parse_cast
from neslter.parsing.ctd.hdr import compile_hdr_files
from neslter.analysis.suna.nut_matchups import suna2nitrate
from neslter.parsing.utils import interpolate_timeseries

def list_suna_files(data_dir, serial_number):
    for fn in os.listdir(data_dir):
        regex = r'A.*SUNA{:04d}.csv'.format(serial_number)
        m = re.match(regex, fn)
        if m:
            yield os.path.join(data_dir, fn)

def suna_start_end(raw_suna_data):
    fns, starts, ends = [], [], []

    for fn, suna_data in raw_suna_data.items():
        fns.append(fn)
        starts.append(suna_data.timestamp.min())
        ends.append(suna_data.timestamp.max())

    suna_se = pd.DataFrame({
        'filename': fns,
        'start': starts,
        'end': ends,
    })
    
    return suna_se

def parse_casts(ctd_dir):
    casts = {}
    md = compile_hdr_files(ctd_dir)
    l = list(list_casts(ctd_dir))
    cast_list = [cn for _, cn in l]
    for cast in cast_list:
        cast_data = parse_cast(ctd_dir,cast)
        assert 'times' in cast_data.columns
        cast_start = pd.to_datetime(md[md.cast == cast].date.iloc[0], utc=True)
        timestamp = cast_start + pd.to_timedelta(cast_data['times'], unit='s')
        cast_data['date'] = timestamp
        cast_data.set_index(timestamp)
        casts[cast] = cast_data
    return md, casts
    
def cast_start_end(casts_data):
    starts, ends, casts = [], [], []
    
    for cast, cast_data in casts_data.items():
        cast_data = casts_data[cast]
        cast_start = cast_data.date.min()
        cast_end = cast_data.date.max()
        casts.append(cast)
        starts.append(cast_start)
        ends.append(cast_end)
    return pd.DataFrame({
        'cast': casts,
        'start': starts,
        'end': ends
    })

def cast2suna_file(suna_se, cast_se):
    result = {}
    
    for cast_row in cast_se.itertuples():
        cast = cast_row.cast
        for _, suna_row in suna_se.iterrows():
            if cast_row.start > suna_row.start and cast_row.end < suna_row.end:
                result[cast] = suna_row.filename

    return result

def generate_suna_profiles(suna_dir, ctd_dir, serial_number, cal_file='a'):
    # parse casts
    print('parsing CTD casts...')
    md, casts_data = parse_casts(ctd_dir)
    # compute starts and ends of cast data
    cast_se = cast_start_end(casts_data)
    # ensure there's a cal file
    cal_file_letter = cal_file.upper()
    cal_path = os.path.join(suna_dir,'SNA{:04d}{}.CAL'.format(serial_number, cal_file_letter))
    assert os.path.exists(cal_path)
    print('found cal file {}'.format(os.path.basename(cal_path)))
    # parse suna data
    raw_suna_data = {} # suna data by filename
    print('parsing suna data ...')
    for path in list_suna_files(suna_dir, serial_number):
        fn = os.path.basename(path)
        print('\r{}'.format(fn),end='',flush=True)
        raw_suna_data[fn] = parse_suna_csv(path)
    # map cast numbers to suna filenames
    suna_se = suna_start_end(raw_suna_data)
    cast2file = cast2suna_file(suna_se, cast_se)
    # compute ts_corrected profile
    print('\napplying temperature and salinity correction...')
    suna_casts = {}
    for cast, file in cast2file.items():
        print('\rcast {}...'.format(cast),end='',flush=True)
        suna_path = os.path.join(suna_dir, file)
        cast_data = casts_data[cast].copy()
        nit = suna2nitrate(cal_path, suna_path, cast_data) # do the ts correction
        nit = nit.loc[~nit.index.duplicated(keep='first')]
        nit = nit[(nit.index >= cast_data.date.min()) & (nit.index <= cast_data.date.max())]
        #it = interpolate_timeseries(nit, cast_data.date)
        #cast_data['suna_nitrate'] = it.nitrate.values
        #cast_data['raw_nitrate'] = it.raw_nitrate.values
        #for ec in ENG_COLUMNS:
        #    cast_data[ec] = it[ec].values
        #suna_casts[cast] = cast_data.dropna(subset=['suna_nitrate'])
        cast_data.set_index(cast_data.date, inplace=True)
        cd = interpolate_timeseries(cast_data, nit.index, interpolation='ffill')
        cd['suna_nitrate'] = nit.nitrate.values
        cd['raw_nitrate'] = nit.raw_nitrate.values
        for ec in ENG_COLUMNS:
            cd[ec] = nit[ec].values
        suna_casts[cast] = cd.dropna()
    print('\nDone')
    return suna_casts

def output_suna_profiles(suna_casts, out_dir, filename_prefix):
    assert os.path.exists(out_dir)
    for cast_number, full_cast in suna_casts.items():
        if len(full_cast) == 0:
            continue
        outpath_prefix = '{}_cast{:03d}'.format(filename_prefix, cast_number)
        upcast = full_cast[full_cast.index >= full_cast.depsm.idxmax()]
        downcast = full_cast[full_cast.index < full_cast.depsm.idxmax()]
        fc_path = os.path.join(out_dir, '{}.csv'.format(outpath_prefix))
        uc_path = os.path.join(out_dir, '{}u.csv'.format(outpath_prefix))
        dc_path = os.path.join(out_dir, '{}d.csv'.format(outpath_prefix))
        full_cast.to_csv(fc_path, index=None)
        upcast.to_csv(uc_path, index=None)
        downcast.to_csv(dc_path, index=None)
