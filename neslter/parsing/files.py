import os
from .utils import safe_makedirs


DATA_ROOT=os.environ.get('DATA_ROOT', '/data')

RAW = 'raw'
PRODUCTS = 'products'
CORRECTED = 'corrected'
ALL = 'all'

FILENAME = 'filename'


class DataNotFound(Exception):
    """Necessary data was not found"""
    pass


class Resolver(object):
    def __init__(self, data_root=None):
        if data_root is None:
            data_root = DATA_ROOT
        self.data_root = data_root
    def raw_directory(self, data_type, cruise=ALL, check_exists=True):
        raw_dir = os.path.join(self.data_root, RAW, cruise, data_type)
        if check_exists and not os.path.exists(raw_dir):
            raise DataNotFound('{} directory not found for {}'.format(data_type, cruise))
        return raw_dir
    def raw_file(self, data_type, name=None, check_exists=True, **kw):
        if name is None: # using None so name can be used as a keyword
            raise ValueError('file name must be provided')
        raw_dir = self.raw_directory(data_type, **kw)
        raw_path = os.path.join(raw_dir, name)
        if check_exists and not os.path.exists(raw_path):
            raise DataNotFound('file {} not found'.format(raw_path))
        return raw_path
    def product_directory(self, data_type, cruise=ALL, makedirs=False):
        proc_dir = os.path.join(self.data_root, PRODUCTS, cruise, data_type)
        if makedirs:
            safe_makedirs(proc_dir)
        return proc_dir
    def product_file(self, data_type, cruise, name=None, extension='json', makedirs=False):
        proc_dir = self.product_directory(data_type, cruise, makedirs=makedirs)
        name_ext = '{}.{}'.format(name, extension)
        return os.path.join(proc_dir, name_ext)
    def corrected_directory(self, data_type, cruise=ALL, makedirs=False):
        corr_dir = os.path.join(self.data_root, CORRECTED, cruise, data_type)
        if makedirs:
            safe_makedirs(corr_dir)
        return corr_dir
    def directories(self, data_type, cruise, skip_raw=False):
        dirs = []
        if not skip_raw:
            dirs.append(self.raw_directory(data_type, cruise))
        dirs.append(self.corrected_directory(data_type, cruise))
        dirs.append(self.product_directory(data_type, cruise))
        return dirs
    def cruises(self):
        c = []
        raw = os.path.join(self.data_root, RAW)
        for fn in sorted(os.listdir(raw)):
            if not os.path.isdir(os.path.join(raw, fn)):
                continue
            if fn != ALL:
                c.append(fn)
        return c

def find_file(directories, filename, extension=None):
    for directory in directories:
        path = os.path.join(directory, filename)
        if extension is not None:
            path = '{}.{}'.format(path, extension)
        if os.path.exists(path):
            return path
    return None

ENDEAVOR = 'Endeavor'
ARMSTRONG = 'Armstrong'
ATLANTIS = 'Atlantis'
SHARP = 'Sharp'
EXPLORER = 'Explorer'

def cruise_to_vessel(cruise):
    lower = cruise.lower()
    if lower.startswith('en'):
        return ENDEAVOR
    elif lower.startswith('ar'):
        return ARMSTRONG
    elif lower.startswith('at'):
        return ATLANTIS
    elif lower.startswith('hrs'):
        return SHARP
    elif lower.startswith('ae'):
        return EXPLORER
    else:
        raise KeyError('cannot determine vessel for {}'.format(cruise))
