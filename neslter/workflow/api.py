from . import logger

import pandas as pd

from neslter.parsing.files import Resolver, find_file 

def read_product_csv(path):
    """file must exist and be a CSV file"""
    df = pd.read_csv(path, index_col=None, encoding='utf-8')
    for c in df.columns:
        if c.lower() in ['date', 'datetime', 'datetime8601']: # FIXME kludgy
            try:
                df[c] = pd.to_datetime(df[c], utc=True)
            except: # not really dates
                pass
    return df

class Workflow(object):
    def find_product(self):
        """return filename and the path to the product CSV or None if not exists"""
        filename = self.filename()
        dirs = self.directories()
        return filename, find_file(dirs, filename, extension='csv')
    def get_product(self):
        """don't override this method"""
        filename, path = self.find_product()
        if path is not None:
            return read_product_csv(path)
        else:
            return self.produce_product()
