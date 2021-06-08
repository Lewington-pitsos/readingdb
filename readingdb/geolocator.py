from readingdb.reading import PositionReading
from typing import Any, Dict, List


class Geolocator():
    @classmethod
    def geolocate(cls, pos_readings: List[Dict[str, Any]]):
        return pos_readings
    
    @classmethod
    def generate_predictions(
        cls, 
        pos_readings: List[Dict[str, Any]], 
        img_readings: List[Dict[str, Any]]
    ):
        snapped = cls.geolocate(pos_readings)


        return img_readings
