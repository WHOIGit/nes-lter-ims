import os
from .utils import safe_makedirs

DATA_ROOT = '/data'

RAW = 'raw'
PRODUCTS = 'products'
ALL = 'all'

FILENAME = 'filename'

class Resolver(object):
    def __init__(self, data_root=None):
        if data_root is None:
            data_root = DATA_ROOT # FIXME get from config file
        self.data_root = data_root
    def raw_directory(self, data_type, cruise=ALL, check_exists=True):
        raw_dir = os.path.join(self.data_root, RAW, cruise, data_type)
        if check_exists and not os.path.exists(raw_dir):
            raise KeyError('{} directory not found for {}'.format(data_type, cruise))
        return raw_dir
    def raw_file(self, data_type, name=None, check_exists=True, **kw):
        if name is None: # using None so name can be used as a keyword
            raise ValueError('file name must be provided')
        raw_dir = self.raw_directory(data_type, **kw)
        raw_path = os.path.join(raw_dir, name)
        if check_exists and not os.path.exists(raw_path):
            raise KeyError('file {} not found'.format(raw_path))
        return raw_path
    def processed_directory(self, data_type, cruise=ALL, makedirs=False):
        proc_dir = os.path.join(self.data_root, RAW, cruise, data_type)
        if makedirs:
            safe_makedirs(proc_dir)
        return proc_dir
    def cruises(self):
        c = []
        raw = os.path.join(self.data_root, RAW)
        for fn in os.listdir(raw):
            if fn != ALL:
                c.append(fn)
        return c

ENDEAVOR = 'Endeavor'
ARMSTRONG = 'Armstrong'

def cruise_to_vessel(cruise):
    lower = cruise.lower()
    if lower.startswith('en'):
        return ENDEAVOR
    elif lower.startswith('ar'):
        return ARMSTRONG
    else:
        raise KeyError('cannot determine vessel for {}'.format(cruise))
