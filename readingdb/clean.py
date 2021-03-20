import copy
from os import read

from readingdb.constants import *

def encoded_value(reading_type, reading_value):
    if reading_type == ReadingTypes.POSITIONAL:
        position = copy.deepcopy(reading_value)

        position[PositionReading.LATITUDE] = int(reading_value[PositionReading.LATITUDE] * PositionReading.ENCODING_COEFFICIENT)
        position[PositionReading.LONGITUDE] = int(reading_value[PositionReading.LONGITUDE] * PositionReading.ENCODING_COEFFICIENT)

        return position

    if reading_type == ReadingTypes.IMAGE:
        return reading_value
    
    if reading_type == ReadingTypes.PREDICTION:
        pred = copy.deepcopy(reading_value)

        for f in PredictionReading.FLOAT_FIELDS:
            if f in pred:
                pred[f] = int(pred[f] * PredictionReading.ENCODING_COEFFICIENT)

        for f in PredictionReading.BOOL_FIELDS:
            if f in pred:
                pred[f] = 1 if pred[f] else 0
        
        return pred

    raise ValueError(f"Unrecognized reading type: {reading_type}")

    return reading_value


def decode_item(item):
    item[Keys.READING] = decoded_value(item[Keys.TYPE], item[Keys.READING])

    return item

def decoded_value(reading_type, reading_value):
    if reading_type == ReadingTypes.POSITIONAL:
        position = copy.deepcopy(reading_value)

        position[PositionReading.LATITUDE] = float(reading_value[PositionReading.LATITUDE]) / PositionReading.ENCODING_COEFFICIENT
        position[PositionReading.LONGITUDE] = float(reading_value[PositionReading.LONGITUDE]) / PositionReading.ENCODING_COEFFICIENT

        return position
    
    if reading_type == ReadingTypes.IMAGE:
        return reading_value

    if reading_type == ReadingTypes.PREDICTION:
        pred = copy.deepcopy(reading_value)

        for f in PredictionReading.FLOAT_FIELDS:
            if f in pred:
                pred[f] = float(pred[f]) / PredictionReading.ENCODING_COEFFICIENT

        for f in PredictionReading.BOOL_FIELDS:
            if f in pred:
                pred[f] = True if pred[f] == 1 else False

        return pred

    raise ValueError(f"Unrecognized reading type: {reading_type}")

    return reading_value
