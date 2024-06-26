import re
import os

import pandas as pd
import numpy as np
from geopy.distance import distance as geo_distance

from .files import Resolver
from .utils import data_table

from .ctd import Ctd

METADATA = 'metadata'

class Stations(object):
    def __init__(self, cruise):
        resolv = Resolver()
        raw_filename = '{}_station_list.xlsx'.format(cruise.upper())
        path = resolv.raw_file(METADATA, raw_filename, cruise=cruise)
        raw_dir = resolv.raw_directory(METADATA, cruise=cruise)
        filenames = os.listdir(raw_dir)
        # use case-sensitive string compare for case-insensitive file systems
        if raw_filename not in filenames:
            raise KeyError('cannot find station metadata at {}'.format(path))
        self.raw_path = path
        self.cruise = cruise
    def station_metadata(self, exclude_waypoints=True):
        columns = ['long_name', 'name', 'latitude', 'longitude', 'depth', 'comments']
        df = pd.read_excel(self.raw_path, index_col=None)
        df.columns = columns
        df['comments'] = df['comments'].fillna('')
        # some 'stations' are just waypoints where there won't be a cast
        if exclude_waypoints:
            df = df[~df['comments'].str.contains('waypoint only')]
        def parse_lon(lon):
            l = parse_ll(lon)
            if l > 0:
                return 0 - l
            return l
        def parse_ll(ll):
            """Parse lat or lon. First checks if decimal degrees,
            Otherwise parse a lat or lon in dec minutes e.g., 40° 32.5'"""
            try:
                return float(ll)
            except ValueError:
                pass
            lon_west = 'W' in ll
            lat_south = 'S' in ll
            ll = re.sub(r'[^\d. ]','',ll).strip()
            deg, min = re.split(r'\s+',ll)
            deg = int(deg)
            frac = float(min) / 60
            l = round(deg + frac, 4)
            if lon_west or lat_south:
                return 0 - l
            else:
                return l
        def parse_depth(d):
            """removes 'm' from depth and parses as float"""
            if pd.isnull(d):
                return np.nan
            return float(re.sub(r'\s*m','',d))
        # compute derived fields
        df['dec_lat'] = df['latitude'].map(parse_ll, na_action='ignore')
        df['dec_lon'] = df['longitude'].map(parse_lon, na_action='ignore')
        df['depth_m'] = df['depth'].map(parse_depth)
        return df
    def to_dataframe(self, exclude_waypoints=True):
        df = self.station_metadata(exclude_waypoints=exclude_waypoints)
        df['latitude'] = df.pop('dec_lat')
        df['longitude'] = df.pop('dec_lon')
        df['depth'] = df.pop('depth_m')
        return df
    def station_locator(self):
        return StationLocator(self.station_metadata())
    def station_distances(self, lat, lon):
        return self.station_locator().station_distances(lat, lon)
    def nearest_station(self, df, lat_col='latitude', lon_col='longitude'):
        return self.station_locator().nearest_station(df, lat_col, lon_col)
    def cast_to_station(self, ctd_metadata):
        return self.station_locator().cast_to_station(ctd_metadata)

class StationLocator(object):
    def __init__(self, station_metadata):
        self.station_metadata = station_metadata
    def station_distances(self, lat, lon):
        distances = []
        index = []
        for station in self.station_metadata.itertuples():
            index.append(station.Index)
            distance = geo_distance([lat,lon], [station.latitude, station.longitude]).km
            distances.append(distance)
        distances = pd.Series(distances, index=index)
        return distances
    def nearest_station(self, df, lat_col='latitude', lon_col='longitude'):
        nearest = []
        distance = []
        index = []
        for point in df.itertuples():
            index.append(point.Index)
            # lat, lon can be NaN when there is no bottle file
            if not pd.isna(getattr(point, lat_col)):
                distances = self.station_distances(getattr(point, lat_col), getattr(point, lon_col))
                min_distance = distances.min()
                if min_distance > 2:
                    nearest.append('')
                    distance.append('NaN')
                else:
                    nearest.append(self.station_metadata.loc[distances.idxmin()]['name'])
                    distance.append(min_distance.round(3))
            else:
                nearest.append('')
                distance.append('NaN')
        df = pd.DataFrame({
            'nearest_station': nearest,
            'distance_km': distance
        }, index=index)
        return df
    def cast_to_station(self, ctd_metadata):
        df = ctd_metadata.copy()
        ns = self.nearest_station(df)
        return df.merge(ns, left_index=True, right_index=True)
