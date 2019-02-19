from neslter.parsing.files import Resolver, find_file

METADATA = 'metadata'

class StationsResolver(Resolver):
    def __init__(self, cruise, **kw):
        super(StationsResolver, self).__init__(**kw)
        self.cruise = cruise
    def find_file(self):
        filename = '{}_stations'.format(self.cruise)
        dirs = self.directories(METADATA, self.cruise)
        return filename, find_file(dirs, filename, extension='csv')