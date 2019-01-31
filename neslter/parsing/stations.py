import re
import os

import pandas as pd
from scipy.spatial.distance import euclidean

from .files import Resolver
from .ctd import Ctd

class Stations(object):
    def __init__(self, cruise):
        filename = '{}_station_list.xlsx'.format(cruise.upper())
        path = Resolver().raw_file('metadata', filename, cruise=cruise)
        assert os.path.exists(path), 'cannot find station metadata at {}'.format(path)
        self.raw_path = path
        self.cruise = cruise
    def station_metadata(self, exclude_waypoints=True):
        columns = ['long_name', 'name', 'latitude', 'longitude', 'depth', 'comments']
        df = pd.read_excel(self.raw_path, index=None, header=None) # assume there's no header
        df.columns = columns
        df['comments'] = df['comments'].fillna('')
        # some 'stations' are just waypoints where there won't be a cast
        if exclude_waypoints:
            df = df[~df['comments'].str.contains('waypoint only')]
        def parse_ll(ll):
            """Parse a lat or lon in dec minutes e.g., 40° 32.5'
            does not parse any N/S/E/W indication"""
            ll = re.sub(r'[^\d. ]','',ll).lstrip()
            deg, min = re.split(r'\s+',ll)
            deg = int(deg)
            frac = float(min) / 60
            return round(deg + frac, 4)
        def parse_depth(d):
            """removes 'm' from depth and parses as int"""
            return int(re.sub(r'\s*m','',d))
        # compute derived fields
        df['dec_lat'] = df['latitude'].map(parse_ll, na_action='ignore') # N
        df['dec_lon'] = 0 - df['longitude'].map(parse_ll, na_action='ignore') # W
        df['depth_m'] = df['depth'].map(parse_depth)
        return df
    def station_distances(self, lat, lon):
        station_md = self.station_metadata()
        distances = []
        index = []
        for station in station_md.itertuples():
            index.append(station.Index)
            distance = euclidean([lat,lon], [station.dec_lat, station.dec_lon])
            distances.append(distance)
        distances = pd.Series(distances, index=index)
        return distances
    def nearest_station(self, df, lat_col='latitude', lon_col='longitude'):
        station_md = self.station_metadata()
        nearest = []
        index = []
        for point in df.itertuples():
            index.append(point.Index)
            distances = self.station_distances(getattr(point, lat_col), getattr(point, lon_col))
            nearest.append(station_md.loc[distances.idxmin()]['name'])
        return pd.Series(nearest, index=index)
    def cast_to_station(self, ctd_metadata=None):
        if ctd_metadata is None:
            ctd_metadata = Ctd(self.cruise).metadata()
        df = ctd_metadata.copy()
        df['nearest_station'] = self.nearest_station(df)
        return df