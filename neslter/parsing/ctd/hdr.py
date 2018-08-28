import re
import os
from glob import glob

import pandas as pd

from .common import CtdTextParser, pathname2cruise_cast

class HdrFile(CtdTextParser):
    def __init__(self, path, parse=True):
        super(HdrFile, self).__init__(path, parse)
    def parse(self):
        super(HdrFile, self).parse()
        self._parse_names()
    def _read_lines(self):
        self.lines = []
        with open(self.path, 'r', encoding='latin-1') as fin:
            for l in fin.readlines():
                if not l.startswith('*END*'):
                    self.lines.append(l.rstrip())
    def _parse_names(self):
        REGEX = r'# name \d+ = ([^:]+): ([^\[]+)(?:\[(.*)\](, .*)?)?'
        names, defns, units, params = set(), {}, {}, {}
        for line in self._lines:
            if not re.search(r'^# name \d+', line):
                continue
            name, defn, unit, param = re.match(REGEX, line).groups()
            defn = defn.rstrip() # FIXME do in regex?
            if param is not None:
                param = param.lstrip(', ') # FIXME do in regex?
            names.add(name)
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
        cr, ca = pathname2cruise_cast(path)
        if cr.lower() == cruise.lower() and int(ca) == int(cast):
            return HdrFile(path)