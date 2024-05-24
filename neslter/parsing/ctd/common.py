import re
import os
import glob as glob

import pandas as pd
import numpy as np

CRUISE_IDX = 1
CAST_IDX = 2

def parse_lat_lon(ll):
    """convert deg/dec minutes into dec"""
    REGEX = r'(\d+)[^\d]+([\d.]+)[^NSEW]*([NSEW])'
    deg, mnts, hemi = re.match(REGEX, ll).groups()
    mult = 1 if hemi in ['N', 'E'] else -1
    deg, mnts = int(deg), float(mnts)
    deg = mult * (deg + (mnts / 60))
    return deg

"""these are used to parse filenames and extract
cruise number and cast number. each is a special
case for a different naming convention used on
NES-LTER vessels"""
CRUISE_CAST_PATHNAME_REGEXES = [
    r'(ar22)(\d\d)\.', # Armstrong 22
    r'(ar24)(\d\d\d)\.', # Armstrong 24a
    r'(ar\d\d[a-c]?)(\d\d\d)\.', # Armstrong 24b/c, 28
    r'(ar\d\d[a-c]?)(\d\d\d+[a-z]*)\.', # Armstrong 16, cast 009a
    r'(ar\d\d[a-c]?).*(\d{3})\.', # Armstrong ar70b_001
    r'(EN\d+).*[Cc]ast(\d+[a-z]*?)(?:_\w+)?\.', # Endeavor 608, 617
    r'([Ee][Nn]\d+)[^\d]+(\d+)(?:_u)?\.', # Endeavor, EN627_028_u.asc
    r'(RB\d+)-(\d{3})\.', # Ron Brown
    r'(tn\d+)-(\d{3})\.', # SPIROPA testing
    r'(at\d+)_(\d{3})\.', # Atlantis
    r'([Hh][Rr][Ss]\d+).*(\d{3})\.', #Sharp
]

def pathname2cruise_cast(pathname, skip_bad_filenames=True):
    fn = os.path.basename(pathname)
    for regex in CRUISE_CAST_PATHNAME_REGEXES:
        m = re.match(regex, fn)
        if m is not None:
            cruise = m.group(CRUISE_IDX)
            cast = m.group(CAST_IDX)
            # handle issue with old filenames for ar24a
            if cruise == 'ar24':
                cruise = 'ar24a'
            cruise = cruise.upper()
            # FIXME hardcoded to deal with problem with EN608 cast "13"
            # if cruise.lower() == 'en608' and cast == '13b':
            #   cast = 14
            # FIXME hardcoded to deal with problem with EN627 cast "1"
            if cruise.lower() == 'en627' and cast == '1':
                cast = 2
            return cruise, cast      
    if not skip_bad_filenames:
        raise ValueError('unable to determine cruise and cast from "{}"'.format(pathname))
    else:
        return None, None

class TextParser(object):
    def __init__(self, path, parse=True, encoding='latin-1'):
        self.path = path
        self.encoding = encoding
        if parse:
            self.parse()
    def parse(self):
        lines = []
        with open(self.path, 'r', encoding=self.encoding) as fin:
            for line in fin.readlines():
                lines.append(line.rstrip())
        self._lines = lines
    def _lines_that_match(self, regex):
        for line in self._lines:
            if re.match(regex, line):
                yield line
    def _line_that_matches(self, regex):
        for line in self._lines_that_match(regex):
            return line

class CtdTextParser(TextParser):
    """parent class of BtlFile and HdrFile"""
    def __init__(self, path, parse_filename=True, **kw):
        self.path = path
        self._parse_filename = parse_filename
        super(CtdTextParser, self).__init__(path, **kw)
    def parse(self):
        super(CtdTextParser, self).parse()
        self._parse_time()
        self._parse_lat_lon()
        if self._parse_filename:
            self._parse_cruise_cast()
    def _parse_time(self):
        line = self._line_that_matches(r'\* NMEA UTC \(Time\)')
        line2 = self._line_that_matches(r'\* System UTC')
        if line is None:
            line = line2
        if line is None:
            self.time = pd.NaT
            return
        time = re.match(r'.*= (.*)', line).group(1)
        self.time = pd.to_datetime(time, utc=True)
    def _parse_lat_lon(self):
        lat_line = self._line_that_matches(r'\* NMEA Latitude')
        lon_line = self._line_that_matches(r'\* NMEA Longitude')
        split_regex = r'.*itude = (.*)'
        if lat_line is not None:
            self.lat = parse_lat_lon(re.match(split_regex, lat_line).group(1))
        else:
            self.lat = np.nan
        if lon_line is not None:
            self.lon = parse_lat_lon(re.match(split_regex, lon_line).group(1))
        else:
            self.lon = np.nan
    def _parse_cruise_cast(self):
        self.cruise, self.cast = pathname2cruise_cast(self.path)
