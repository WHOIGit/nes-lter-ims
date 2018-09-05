import numpy as np
import pandas as pd

def validate_chl(df):
    q = df['fd_calibration']
    p = df['tau_calibration']
    u = df['rb_blank']
    v = df['ra_blank']
    k = df['vol_extracted']
    i = df['vol_filtered']
    n = df['dilution_during_reading']

    expected_chl = ( q * p / (p - 1) * (u - v) * k / i ) / n
    assert np.allclose(df['chl'], expected_chl), 'unexpected chl value(s)'

    expected_phaeo = ( q * p / (p - 1) * (p * v - u) * k / i ) / n
    assert np.allclose(df['phaeo'], expected_phaeo), 'unexpected phaeo value(s)'

def average_replicates(chl, replicates=['a','b'], var='chl'):
    assert var in ['chl','phaeo'], 'var must be chl or phaeo'
    replicates = set(replicates)
    rows = []
    for i, sdf in chl.groupby(['cruise','cast','niskin']):
        existing_reps = set(sdf['replicate'])
        if replicates.intersection(existing_reps) != replicates:
            continue
        sdf_reps = sdf[sdf['replicate'].isin(replicates)]
        var_average = sdf_reps[var].mean()
        row = i + (var_average,)
        rows.append(row)
    return pd.DataFrame(rows, columns=['cruise','cast','niskin',var])