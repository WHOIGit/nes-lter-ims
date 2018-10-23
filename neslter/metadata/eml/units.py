from jinja2 import TemplateNotFound

from .utils import get_j2_environment

class EmlUnit(object):
    def __init__(self, name):
        assert name is not None, 'unit must have name'
        self.name = name
        if self.is_custom:
            self.standard_or_custom = 'custom'
        else:
            self.standard_or_custom = 'standard'
    @property
    def is_custom(self):
        try:
            template = self._get_stmml_template()
            return True
        except TemplateNotFound:
            return False
    def _get_stmml_template(self):
        template_name = '{}.xml'.format(self.name)
        j2_env = get_j2_environment(dir='stmml_units')
        return j2_env.get_template(template_name)
    def to_stmml(self):
        assert self.is_custom(), 'standard units do not have stmml representations'
        return self._get_stmml_template().render({})

class EmlMeasurementScale(object):
    def __init__(self, unit=None, is_interval=False, numeric_domain=None,
            is_string=False, is_date=False, precision=None, definition=''):
        assert numeric_domain in [None, 'real', 'integer'], \
            'unrecognized numeric domain {}'.format(numeric_domain)
        assert not is_string or (is_string and numeric_domain is None), \
            'text has no numeric domain'
        assert precision is None or numeric_domain == 'real', \
            'non-real numeric domains cannot have precision'
        if isinstance(unit, str):
            self.unit = EmlUnit(unit)
        else:
            self.unit = unit
        self.is_interval = is_interval
        self.ratio_or_interval = 'interval' if is_interval else 'ratio'
        self.is_real = numeric_domain == 'real'
        self.is_integer = numeric_domain == 'integer'
        self.is_string = is_string
        self.is_date = is_date
        self.precision = precision
        self.definition = definition
    def __repr__(self):
        if self.is_date:
            desc = 'date'
        elif self.is_string:
            desc = 'string'
        elif self.is_real:
            desc = 'real {}'.format(self.ratio_or_interval)
        elif self.is_integer:
            desc = 'integer'
        else:
            desc = '' # don't raise an error in __repr__
        return '<EmlMeasurementScale {}>'.format(desc)
    @property
    def xsd_type(self):
        if self.is_string:
            return 'string'
        elif self.is_real:
            return 'double'
        elif self.is_integer:
            return 'integer'
        elif self.is_date:
            return 'date'
    # useful constructors
    @staticmethod
    def string(definition=''):
        return EmlMeasurementScale(is_string=True, definition=definition)
    @staticmethod
    def real(unit=None, is_interval=False):
        return EmlMeasurementScale(numeric_domain='real', unit=unit, is_interval=is_interval)
    @staticmethod
    def date(format=None):
        # FIXME do something with format
        return EmlMeasurementScale(is_date=True)
    @staticmethod
    def degree(precision=None):
        return EmlMeasurementScale(is_interval=True, numeric_domain='real', unit='degree',
            precision=precision)
    @staticmethod
    def integer(unit=None, is_interval=False):
        return EmlMeasurementScale(unit=unit, numeric_domain='integer', is_interval=is_interval)