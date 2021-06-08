from readingdb.reading import PositionReading
from typing import Any, List


class Geolocator():
    @classmethod
    def geolocate(cls, pos_readings: List[PositionReading]):
        return pos_readings