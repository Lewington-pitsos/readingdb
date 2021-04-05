
from decimal import Decimal
from typing import Any, Dict, List
from readingdb import route

from readingdb.constants import *
from readingdb.conditions import *
from readingdb.clean import encode_float, encode_bool, decode_bool, decode_float
class Reading():
    def __init__(self, id: int, route_id: int, date: int, readingType: str) -> None:
        self.id: int = id
        self.route_id: int = route_id
        self.date: int = date
        self.readingType: str = readingType

    def item_data(self):
        return {
            ReadingKeys.READING_ID: self.id,
            ReadingRouteKeys.ROUTE_ID: self.route_id,
            ReadingKeys.TYPE: self.readingType,  
            ReadingKeys.TIMESTAMP: self.date, 
        }


class ImageReading(Reading):
    def __init__(self, id: int, route_id: int, date: int, readingType: str, url: str) -> None:
        super().__init__(id, route_id, date, readingType)

        self.url: str = url

    def item_data(self):
        data = super().item_data()

        data[ReadingKeys.READING] = {
            ImageReadingKeys.FILENAME: self.url
        }

        return data

    def decode(self, item: Dict[str, Any]):
        pass

class PositionReading(Reading):
    def __init__(self, id: int, route_id: int, date: int, readingType: str, lat: int, long: int) -> None:
        super().__init__(id, route_id, date, readingType)

        self.lat: int = lat
        self.long: int = long

    def item_data(self):
        data = super().item_data()

        data[ReadingKeys.READING] = {
            PositionReading.LATITUDE: self.lat,
            PositionReading.LONGITUDE: self.long
        }

        return data

    def decode(self, item: Dict[str, Any]):
        pass

class PredictionReading(PositionReading):
    def __init__(
        self, id: int, 
        route_id: int, 
        date: int, 
        readingType: str, 
        lat: int, 
        long: int,
        url: str,
        predictionBinaries: Dict[str, bool],
        predictionConfidences: Dict[str, float],
    ):
        super().__init__(id, route_id, date, readingType, lat, long)    

        self.url: str = url
        self.predictionBinaries: Dict[str, bool] = predictionBinaries
        self.predictionConfidences: Dict[str, bool] = predictionConfidences
    
    def decode(self, item: Dict[str, Any]):
        super().decode(item)

        for k, v in item[ReadingKeys.READING]:
            if k in CONDITION_BIARIES:
                item[ReadingKeys.READING][k] = decode_bool(v)
            if k in CONDITION_CONFS:
                item[ReadingKeys.READING][k] = decode_float(v)


    def item_data(self):
        data = super().item_data()

        data[ReadingKeys.READING][ImageReadingKeys.FILENAME] = self.url

        for k, v in self.predictionBinaries.items():
            data[ReadingKeys.READING][k] = encode_bool(v)

        for k, v in self.predictionConfidences.items():
            data[ReadingKeys.READING][k] = encode_float(v)

        return data