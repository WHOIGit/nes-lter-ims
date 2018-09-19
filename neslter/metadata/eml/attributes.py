import pandas as pd

from .utils import get_j2_environment
from .types import xsd_type, precision2eml
from .units import EmlUnit

def is_latlon(name):
    """infer whether a variable is a lat/lon, based on the name"""
    return name.lower() in ['latitude', 'longitude', 'lat', 'lon']

class EmlAttribute(object):
    def __init__(self, name, dtype=None, xsd_type=None, unit=None,
        definition='', precision=None, infer_latlon=True):
        assert name is not None, 'name required'
        self.name = name
        if infer_latlon:
            self.is_latlon = is_latlon(name)
        if self.is_latlon:
            self.xsd_type = 'double'
            self.unit = EmlUnit('degree', is_interval=True)
        else:
            assert dtype is not None or xsd_type is not None, 'must specify type'
            if xsd_type is not None:
                self.xsd_type = xsd_type
            else:
                self.xsd_type = xsd_type(dtype)
            assert unit is not None, 'unit is required'
            self.unit = unit
        self.precision = precision
        self.definition = definition
    def to_eml(self):
        j2_env = get_j2_environment()
        context = {
            'name': self.name,
            'is_latlon': self.is_latlon,
            'xsd_type': self.xsd_type,
            'definition': self.definition,
            'unit': self.unit.name,
            'ratio_or_interval': self.unit.ratio_or_interval,
            'standard_or_custom_unit': self.unit.standard_or_custom,
        }
        if self.precision is not None:
            context['precision'] = precision2eml(self.precision)
        template = j2_env.get_template('attribute.template')
        return template.render(context)
