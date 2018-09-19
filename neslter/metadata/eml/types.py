import re

import numpy as np

# dtype mapping to XML Schema datatypes

object_type = np.dtype('O')
datetime_type = np.dtype('<M8[ns]')
float_type = np.dtype('float64')
int_type = np.dtype('int32')

XSD_TYPE_MAP = {
    object_type: 'string',
    datetime_type: 'date',
    float_type: 'double',
    int_type: 'integer'
}

def xsd_type(dtype):
    """return the XML Schema datatype for a given dtype"""
    return XSD_TYPE_MAP.get(dtype,'string')

def precision2eml(precision):
    """convert e.g., 3 to 1e-3 where 3 is the
    number of decimal places"""
    # FIXME is that correct?
    return '1e-{}'.format(precision)

def infer_precision(string_arraylike, as_eml=True):
    """given an arraylike of string representations of
    floating point numbers, infer the precision (number
    of decimal places"""
    def count_decimals(string):
        if np.isnan(float(string)):
            return 0
        return len(re.sub(r'.*\.','',string))
    precision = np.max([count_decimals(s) for s in string_arraylike])
    return precision
