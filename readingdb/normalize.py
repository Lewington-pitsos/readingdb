import copy

from readingdb.constants import *

def encoded_value(reading_type, reading_value):
    if reading_type == ReadingTypes.POSITIONAL:
        position = copy.deepcopy(reading_value)

        position[PositionReading.LATITUDE] = int(reading_value[PositionReading.LATITUDE] * PositionReading.ENCODING_COEFFICIENT)
        position[PositionReading.LONGITUDE] = int(reading_value[PositionReading.LONGITUDE] * PositionReading.ENCODING_COEFFICIENT)

        return position
    
    raise ValueError(f"Unrecognized reading type: {reading_type}")

    return reading_value


def decoded_value(reading_type, reading_value):
    if reading_type == ReadingTypes.POSITIONAL:
        position = copy.deepcopy(reading_value)

        position[PositionReading.LATITUDE] = float(reading_value[PositionReading.LATITUDE]) / PositionReading.ENCODING_COEFFICIENT
        position[PositionReading.LONGITUDE] = float(reading_value[PositionReading.LONGITUDE]) / PositionReading.ENCODING_COEFFICIENT

        return position
    
    raise ValueError(f"Unrecognized reading type: {reading_type}")

    return reading_value
