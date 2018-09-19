from jinja2 import Environment, PackageLoader, select_autoescape

from .types import xsd_type, precision2eml

def is_latlon(name):
    return name.lower() in ['latitude', 'longitude', 'lat', 'lon']

class EmlAttribute(object):
    def __init__(self, name, dtype=None, xsd_type=None, unit=None, is_interval=False,
        is_standard_unit=True, definition='', precision=None, infer_latlon=True):
        assert name is not None, 'name required'
        self.name = name
        if infer_latlon:
            self.is_latlon = is_latlon(name)
        if not self.is_latlon:
            assert dtype is not None or xsd_type is not None, 'must specify type'
            if xsd_type is not None:
                self.xsd_type = xsd_type
            else:
                self.xsd_type = xsd_type(dtype)
        else:
            self.xsd_type = 'double'
        if is_interval:
            self.ratio_or_interval = 'interval'
        else:
            self.ratio_or_interval = 'ratio'
        if is_standard_unit:
            self.standard_or_custom_unit = 'standard'
        else:
            self.standard_or_custom_unit = 'custom'
        self.unit = unit
        self.precision = precision
        self.definition = definition
    def to_eml(self):
        j2_env = Environment(
            loader=PackageLoader('neslter.metadata.eml', 'templates'),
            autoescape=select_autoescape(['xml'])
        )
        j2_env.trim_blocks = True
        context = {
            'name': self.name,
            'is_latlon': self.is_latlon,
            'xsd_type': self.xsd_type,
            'unit': self.unit,
            'ratio_or_interval': self.ratio_or_interval,
            'standard_or_custom_unit': self.standard_or_custom_unit,
            'definition': self.definition,
        }
        if self.precision is not None:
            context['precision'] = precision2eml(self.precision)
        template = j2_env.get_template('attribute.template')
        return template.render(context)
