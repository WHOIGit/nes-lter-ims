import numpy as np
import pandas as pd

def validate_chl(df):
    """validate that chl and phaeo values are correct by computing
    them from other columns, as in the source spreadsheet.
    param: df = parsed chl dataframe"""
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

def average_replicates(chl, replicates=['a','b'], var='chl', over='any'):
    """average chl or phaeo over the given replicates. for example
    to average phaeo over replicates a and b, call it like
    average_replicates(df, replicates=['a','b'], var='phaeo')
    param: chl = parsed chl dataframe
    param: over = whether to require all replicates be present ('all')
    or whether to also average replicates if only some are present ('any')"""
    assert var in ['chl', 'phaeo'], 'var must be chl or phaeo'
    assert over in ['any','all'], 'over must be any or all'
    replicates = set(replicates)
    rows = []
    # group by cruise, cast, niskin
    for ccn, sdf in chl.groupby(['cruise','cast','niskin','filter_mesh_size']):
        # for each c/c/n
        # make sure we have all the given replicates
        existing_reps = set(sdf['replicate'])
        isxn = replicates.intersection(existing_reps)
        if over == 'all' and isxn != replicates:
            continue
        elif over == 'any' and not len(isxn) > 0:
            continue
        # remove all rows except the replicates we want
        sdf_reps = sdf[sdf['replicate'].isin(replicates)]
        # average the variable
        var_average = sdf_reps[var].mean()
        # construct the output row
        row = ccn + (var_average,)
        rows.append(row)
    return pd.DataFrame(rows, columns=['cruise','cast','niskin','filter_mesh_size',var])