import numpy as np
from scipy.io import savemat
from pandas.api.types import is_datetime64_any_dtype

from neslter.parsing.utils import datetime_to_datenum

def df_to_mat(df, filename, convert_dates=True):
    data = {}
    for c in df.columns:
        if convert_dates and is_datetime64_any_dtype(df[c]):
            values = [datetime_to_datenum(dt) for dt in df[c]]
        else:
            values = df[c]
        data[c] = np.array(values)
    savemat(filename, data)
