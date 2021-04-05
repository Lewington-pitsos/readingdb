import json
import copy
from decimal import Decimal
from os import read

import numpy as np

from readingdb.constants import *


def encode_float(value: float) -> Decimal:
    return Decimal(str(value))

def encode_bool(value: bool) -> int:
    return 1 if value else 0

def decode_float(value: Decimal) -> float:
    return float(value)

def decode_bool(value: int) -> bool:
    return value == 1

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
    item[ReadingKeys.READING] = decoded_value(item[ReadingKeys.TYPE], item[ReadingKeys.READING])

    return item

def encoded_route_item(user_id, route_id, route_name=None, sample_data=None):
    route = {
        RouteKeys.USER_ID: user_id,
        ReadingRouteKeys.ROUTE_ID: route_id
    }

    if sample_data:
        encoded_sample_data = {}

        for k, v in sample_data.items():
            encoded_sample_data[k] = encoded_value(k, v)

        route[RouteKeys.SAMPLE_DATA] = encoded_sample_data
    
    if route_name:
        route[RouteKeys.NAME] = route_name

    return route
    
def decoded_route_item(item):

    if RouteKeys.SAMPLE_DATA in item:
        decoded_sample_data = {}
        for k, v in item[RouteKeys.SAMPLE_DATA].items():
            decoded_sample_data[k] = decoded_value(k, v)
        
        item[RouteKeys.SAMPLE_DATA] = decoded_sample_data

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