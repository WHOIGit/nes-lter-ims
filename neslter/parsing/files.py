import os

DATA_ROOT = r'D:\nes-lter-ims-test-data\root'

RAW = 'raw'
PRODUCTS = 'products'
ALL = 'all'

class Resolver(object):
    def __init__(self, data_root=None):
        if data_root is None:
            data_root = DATA_ROOT # FIXME get from config file
        self.data_root = data_root
    def raw_directory(self, data_type, cruise=ALL, check_exists=True):
        raw_dir = os.path.join(self.data_root, RAW, cruise, data_type)
        if check_exists and not os.path.exists(raw_dir):
            raise ValueError('{} directory not found for {}'.format(data_type, cruise))
        return raw_dir

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
