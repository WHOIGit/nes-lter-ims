import pandas as pd

from .utils import get_j2_environment, pretty_print_xml
from .types import xsd_type, precision2eml
from .units import EmlUnit, EmlMeasurementScale

def is_latlon(name):
    """infer whether a variable is a lat/lon, based on the name"""
    return name.lower() in ['latitude', 'longitude', 'lat', 'lon']

class EmlAttribute(object):
    def __init__(self, name, measurement_scale=None, definition='', infer_latlon=True):
        assert name is not None, 'name required'
        self.name = name
        self.is_latlon = is_latlon(name)
        if self.is_latlon:
            self.measurement_scale = EmlMeasurementScale.degree()
        else:
            self.measurement_scale = measurement_scale
        self.definition = definition
    def to_eml(self, pretty_print=True):
        j2_env = get_j2_environment()
        template = j2_env.get_template('attribute.template')
        xml = template.render({
            'attr': self,
            'ms': self.measurement_scale
            })
        if pretty_print:
            return pretty_print_xml(xml)
        else:
            return xml
    def __str__(self):
        return '<EmlAttribute: {}>'.format(self.name)
    def __repr__(self):
        return self.__str__()
    # useful constructors
    @staticmethod
    def string(name, definition=''):
        return EmlAttribute(name, EmlMeasurementScale.string(definition=definition), definition=definition)
    @staticmethod
    def real(name, unit=None, is_interval=False, **kw):
        return EmlAttribute(name, EmlMeasurementScale.real(unit=unit, is_interval=is_interval), **kw)
    @staticmethod
    def date(name, format=None, **kw):
        return EmlAttribute(name, EmlMeasurementScale.date(format=format), **kw)
    @staticmethod
    def degree(name, precision=None, **kw):
        return EmlAttribute(name, EmlMeasurementScale.degree(precision=precision), **kw)
    @staticmethod
    def latitude(**kw):
        return EmlAttribute.degree('latitiude', **kw)
    @staticmethod
    def longitude(**kw):
        return EmlAttribute.degree('longitude', **kw)
    @staticmethod
    def integer(name, is_interval=False, **kw):
        return EmlAttribute(name, EmlMeasurementScale.integer(is_interval=is_interval), **kw)