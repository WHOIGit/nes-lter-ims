from jinja2 import TemplateNotFound

from .utils import get_j2_environment

class EmlUnit(object):
    def __init__(self, name, is_interval=False):
        assert name is not None, 'unit must have name'
        self.name = name
        if is_interval:
            self.ratio_or_interval = 'interval'
        else:
            self.ratio_or_interval = 'ratio'
        if self.is_custom():
            self.standard_or_custom = 'custom'
        else:
            self.standard_or_custom = 'standard'
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
        return self.get_stmml_template().render({})