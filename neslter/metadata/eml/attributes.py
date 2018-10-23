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
        if infer_latlon and is_latlon(name):
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
        return '<EmlAttribute: {} {}>'.format(self.name, self.measurement_scale)
    def __repr__(self):
        return self.__str__()
    # useful constructors
    @staticmethod
    def string(name, definition='', **kw):
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
    def integer(name, unit=None, is_interval=False, **kw):
        return EmlAttribute(name, EmlMeasurementScale.integer(unit=unit, is_interval=is_interval), **kw)

# pandas convenience methods

def attribute_from_series(series, definition=None, **kw):
    DEFAULT_UNIT = '______'
    xtype = xsd_type(series.dtype)
    if xtype == 'string':
        return EmlAttribute.string(series.name, definition=definition, **kw)
    elif xtype == 'double':
        if not 'unit' in kw:
            kw['unit'] = DEFAULT_UNIT
        return EmlAttribute.real(series.name, definition=definition, **kw)
    elif xtype == 'date':
        return EmlAttribute.date(series.name, definition=definition, **kw) 
    elif xtype == 'integer':
        return EmlAttribute.integer(series.name, definition=definition, **kw)
    else:
        raise ValueError('xsd type not recognized. this should not happen')

def attributes_from_dataframe(df, definitions={}, kws={}):
    for column in df.columns:
        series = df[column]
        # if no definition is given, use the column name to provide a placeholder
        definition = definitions.get(column, column)
        kw = kws.get(column, {})
        yield attribute_from_series(series, definition=definition, **kw)