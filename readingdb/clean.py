import json
import copy
from decimal import Decimal
from os import read

import numpy as np

from readingdb.constants import *

def encoded_dict(encoding_cls, value_dict):
    clone = copy.deepcopy(value_dict)

    for f in encoding_cls.FLOAT_FIELDS:
        if f in clone:
            clone[f] = Decimal(str(clone[f]))
    
    for f in encoding_cls.BOOL_FIELDS:
        if f in clone:
            clone[f] = 1 if clone[f] else 0
    
    return clone

def encoded_value(reading_type, reading_value):
    if reading_type == ReadingTypes.IMAGE:
        return reading_value

    if reading_type == ReadingTypes.POSITIONAL:
        return encoded_dict(PositionReading, reading_value)
    if reading_type == ReadingTypes.PREDICTION:
        return encoded_dict(PredictionReading, reading_value)

    raise ValueError(f"Unrecognized reading type: {reading_type}")

    return reading_value


def decode_item(item):
    item[Keys.READING] = decoded_value(item[Keys.TYPE], item[Keys.READING])

    return item


def decoded_dict(decoding_cls, value_dict):
    clone = copy.deepcopy(value_dict)

    for f in decoding_cls.FLOAT_FIELDS:
        if f in clone:
            clone[f] = float(clone[f]) 
            
    for f in decoding_cls.BOOL_FIELDS:
        if f in clone:
            clone[f] = True if clone[f] == 1 else False
    return clone

def decoded_value(reading_type, reading_value):
    if reading_type == ReadingTypes.IMAGE:
        return reading_value

    if reading_type == ReadingTypes.POSITIONAL:
        return decoded_dict(PositionReading, reading_value)
    if reading_type == ReadingTypes.PREDICTION:
        return decoded_dict(PredictionReading, reading_value)

    raise ValueError(f"Unrecognized reading type: {reading_type}")

    return reading_value

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return super(CustomJSONEncoder, self).encode(bool(obj))
        if isinstance(obj, Decimal):
            return int(obj)

        return super(CustomJSONEncoder, self).default(obj)