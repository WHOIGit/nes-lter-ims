import re
import os
from glob import glob

import pandas as pd

from .common import CtdTextParser, pathname2cruise_cast

class HdrFile(CtdTextParser):
    def __init__(self, path, **kw):
        super(HdrFile, self).__init__(path, **kw)
    def parse(self):
        super(HdrFile, self).parse()
        self._parse_names()
    def _read_lines(self):
        self._lines = []
        with open(self.path, 'r', encoding='latin-1') as fin:
            for l in fin.readlines():
                if not l.startswith('*END*'):
                    self._lines.append(l.rstrip())
    def _parse_names(self):
        REGEX = r'# name \d+ = ([^:]+): ([^\[]+)(?:\[(.*)\](, .*)?)?'
        names, defns, units, params = [], {}, {}, {}
        for line in self._lines:
            if not re.search(r'^# name \d+', line):
                continue
            name, defn, unit, param = re.match(REGEX, line).groups()
            defn = defn.rstrip() # FIXME do in regex?
            if param is not None:
                param = param.lstrip(', ') # FIXME do in regex?
            names.append(name)
            defns[name] = defn
            units[name] = unit
            params[name] = params
        self.names = names
        self.definitions = defns
        self.units = units
        self._params = params
    ## accessors
    def definition(self, name):
        return self.definitions[name]
    def units(self, name):
        return self.units[name]

def find_hdr_file(dir, cruise, cast):
    for path in glob(os.path.join(dir, '*.hdr')):
        cr, ca = pathname2cruise_cast(path, skip_bad_filenames=True)
        if cr is None:
            continue
        if cr.lower() == cruise.lower() and int(ca) == int(cast):
            return HdrFile(path)

def compile_hdr_files(hdr_dir):
    cruises, casts, times, lats, lons = [], [], [], [], []
    for path in glob(os.path.join(hdr_dir, '*.hdr')):
        hf = HdrFile(path)
        cruises.append(hf.cruise)
        casts.append(hf.cast)
        times.append(hf.time)
        lats.append(hf.lat)
        lons.append(hf.lon)
    df = pd.DataFrame({
        'cruise': cruises,
        'cast': casts,
        'date': pd.to_datetime(times, utc=True),
        'latitude': lats,
        'longitude': lons
    }).dropna()
    try:
        df['cast'] = df['cast'].astype(int)
    except ValueError:
        df['cast'] = df['cast'].astype(str)
    df = df.sort_values('cast')
    df.index = range(len(df))
    return df
    
