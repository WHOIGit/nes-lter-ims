import numpy as np
from scipy.io import savemat

from neslter.parsing.utils import datetime_to_datenum

def df_to_mat(df, filename, convert_dates=[]):
    data = {}
    for c in df.columns:
        if c in convert_dates:
            values = [datetime_to_datenum(dt) for dt in df[c]]
        else:
            values = df[c]
        data[c] = np.array(values)
    savemat(filename, data)