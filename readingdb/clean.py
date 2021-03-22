import copy
from os import read

from readingdb.constants import *

def encoded_dict(encoding_cls, value_dict):
    clone = copy.deepcopy(value_dict)

    for f in encoding_cls.FLOAT_FIELDS:
        if f in clone:
            clone[f] = int(clone[f] * encoding_cls.ENCODING_COEFFICIENT)
    
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
            clone[f] = float(clone[f]) / decoding_cls.ENCODING_COEFFICIENT

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
