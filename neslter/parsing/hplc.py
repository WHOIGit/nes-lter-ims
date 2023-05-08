import os
import json
from glob import glob

import numpy as np
import pandas as pd

from neslter.parsing.files import DataNotFound

MAPPINGS = {
    "mappings": {
        "Cruise ID": "cruise",
        "Unnamed: 1": "date",
        "Latitude": "latitude",
        "Longitude": "longitude",
        "Sampling Depth (meters)": "depth",
        "Station": "cast",
        "Bottle Number": "niskin",
        "Sample Label": "sample_id",
        "GSFC Lab sample code": "alternate_sample_id",
        "Unnamed: 9": "project_id",
        "Unnamed: 10": "replicate",
        "Volume filtered (ml)": "vol_filtered",
        "[Tot_Chl_a]": "Tot_Chl_a",
        "[Tot_Chl_b]": "Tot_Chl_b",
        "[Tot_Chl_c]": "Tot_Chl_c",
        "[Alpha_beta_Car]": "alpha-beta-Car",
        "[But fuco]": "But-fuco",
        "[Hex fuco]": "Hex-fuco",
        "[Allo]": "Allo",
        "[Diadino]": "Diadino",
        "[Diato]": "Diato",
        "[Fuco]": "Fuco",
        "[Perid]": "Perid",
        "[Zea]": "Zea",
        "[MV_Chl_a]": "MV_Chl_a",
        "[DV_Chl_a]": "DV_Chl_a",
        "[Chlide_a]": "Chlide_a",
        "[MV_Chl _b]": "MV_Chl_b",
        "[DV_Chl_b]": "DV_Chl_b",
        "[Chl c1c2]": "Chl_c1c2",
        "[Chl_c3]": "Chl_c3",
        "[Lut]": "Lut",
        "[Neo]": "Neo",
        "[Viola]": "Viola",
        "[Phytin_a]": "Phytin_a",
        "[Phide_a]": "Phide_a",
        "[Pras]": "Pras",
        "[Gyro]": "Gyro",
        "[TChl]": "TChl",
        "[PPC]": "PPC",
        "[PSC]": "PSC",
        "[PSP]": "PSP",
        "[TCar]": "TCar",
        "[TAcc]": "TAcc",
        "[TPg]": "TPg",
        "[DP]": "DP",
        "[TAcc]/[Tchla]": "TAcc_TChla",
        "[PSC]/[TCar]": "PSC_TCar",
        "[PPC]/[TCar]": "PPC_TCar",
        "[TChl]/[TCar]": "TChl_TCar",
        "[PPC]/[Tpg]": "PPC_TPg",
        "[PSP]/[TPg]": "PSP_TPg",
        "[TChl a]/[TPg]": "TChla_Tpg",
        "comments": "comments",
        "other": "comments2",
        "other.1": "comments3",
        "Indicate if filters are replicates": "R",
        "date": "date"
    },
    "columns": [
        "cruise",
        "date",
        "latitude",
        "longitude",
        "depth",
        "cast",
        "niskin",
        "sample_id",
        "alternate_sample_id",
        "project_id",
        "replicate",
        "vol_filtered",
        "Tot_Chl_a",
        "Tot_Chl_b",
        "Tot_Chl_c",
        "alpha-beta-Car",
        "But-fuco",
        "Hex-fuco",
        "Allo",
        "Diadino",
        "Diato",
        "Fuco",
        "Perid",
        "Zea",
        "MV_Chl_a",
        "DV_Chl_a",
        "Chlide_a",
        "MV_Chl_b",
        "DV_Chl_b",
        "Chl_c1c2",
        "Chl_c3",
        "Lut",
        "Neo",
        "Viola",
        "Phytin_a",
        "Phide_a",
        "Pras",
        "Gyro",
        "TChl",
        "PPC",
        "PSC",
        "PSP",
        "TCar",
        "TAcc",
        "TPg",
        "DP",
        "TAcc_TChla",
        "PSC_TCar",
        "PPC_TCar",
        "TChl_TCar",
        "PPC_TPg",
        "PSP_TPg",
        "TChla_Tpg",
        "comments",
        "comments2",
        "comments3"
    ]
}

def hplc_report_paths(hplc_dir):
    return glob(os.path.join(hplc_dir, 'Sosik*report.xlsx'))
    #return [ 'Sosik08-15report.xlsx' ]

def parse_report(report_path):
    if (not os.path.exists(report_path)):
        raise DataNotFound('Report path not found at {}'.format(report_path))

    Y = 'Year'
    M = 'Month'
    D = 'Day of Gregorian Month'
    T = 'GMT Time'

    report = pd.read_excel(report_path, skiprows=8, dtype={
        Y: str,
        M: str,
        D: str,
        T: str
    })

    # report file contains invalid time fields, ie 6:40:00 AM, instead of 06:40
    # minutes must be padded with a leading zero before passed to pd.to_datetime
    report[T] = report[T].str.split(':', n=2).str[:2].str.join(':')
    report[T] = report[T].str.zfill(5)
    # parse date fields
    dates = report[M] + ' ' + report[D] + ' ' + report[Y] + ' ' + report[T]
    report['date'] = pd.to_datetime(dates, utc=True)

    # map column names
    mappings = MAPPINGS['mappings']

    for c in report.columns:
        if c not in mappings:
            report.pop(c)
    
    report.columns = [ mappings[c] for c in report.columns ]
    
    # produce replicate column
    report.sort_values(['cruise','cast','niskin'], inplace=True)

    R = report.pop('R')
    is_a = (R == 'S') | ((R == 'D') & (R.shift(-1) == 'D'))

    report['replicate'] = np.where(is_a, 'a', 'b')

    # add project_id
    report['project_id'] = 'NESLTER'

    # reorder columns
    report = report[MAPPINGS['columns']]

    # consolidate the comments columns
    report['comments'].fillna('', inplace=True)
    report['comments2'].fillna('', inplace=True)
    report['comments3'].fillna('', inplace=True)
    report['comments'] = report.pop('comments') + ' ' \
        + report.pop('comments2') + ' ' + report.pop('comments3')
    report['comments'] = report['comments'].str.strip()
 
    return report

def parse_hplc(hplc_dir):
    dfs = []
    for report_path in hplc_report_paths(hplc_dir):
        dfs.append(parse_report(report_path))
    result = pd.concat(dfs)
    result = result.replace(-8888,0)
    return result