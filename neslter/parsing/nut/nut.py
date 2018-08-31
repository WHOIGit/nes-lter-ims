import numpy as np
import pandas as pd

from ..utils import clean_column_names, dropna_except, format_dataframe

RAW_COLS = ['Number', 'Cruise', 'Cast', 'Sample ID', 'Nitrate', 'Ammonium',
       'Phosphate', 'Silicate', 'Comments']

NUT_COLS = ['nitrate', 'ammonium', 'phosphate', 'silicate']

def parse_nut(nut_xl_path):
    df = pd.read_excel(nut_xl_path, skiprows=[0,1])
    assert set(df.columns) == set(RAW_COLS), 'nut spreadsheet does not contain expected columns'
    df = clean_column_names(df, {
        'Number': 'nutrient_number',
        })
    df = dropna_except(df, ['comments'])
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
    return df

def format_nut(df):
    prec = { c: 3 for c in NUT_COLS }
    return format_dataframe(df, precision=prec)