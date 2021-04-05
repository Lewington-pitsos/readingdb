import abc
from os import read
from typing import Any, Dict

from readingdb.constants import *
from readingdb.conditions import *
from readingdb.clean import encode_float, encode_bool, decode_bool, decode_float


class AbstractReading(abc.ABC):

    @abc.abstractmethod
    def item_data(self) -> Dict[str, Any]:

        raise ValueError("not implemented")

    @abc.abstractclassmethod
    def decode(cls, item: Dict[str, Any]):

        raise ValueError("not implemented")
class Reading(AbstractReading):
    def __init__(self, id: int, route_id: str, date: int, readingType: str) -> None:
        self.id: int = id
        self.route_id: str = route_id
        self.date: int = date
        self.readingType: str = readingType

    def item_data(self):
        return {
            ReadingKeys.READING_ID: self.id,
            ReadingRouteKeys.ROUTE_ID: self.route_id,
            ReadingKeys.TYPE: self.readingType,  
            ReadingKeys.TIMESTAMP: self.date, 
        }

    @classmethod
    def decode(cls, item: Dict[str, Any]):
        item[ReadingKeys.READING_ID] = int(item[ReadingKeys.READING_ID])
        item[ReadingKeys.TIMESTAMP] = int(item[ReadingKeys.TIMESTAMP])

        

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

    @classmethod
    def decode(cls, item: Dict[str, Any]):
        super().decode(item)
        pass

class PositionReading(Reading):
    def __init__(self, id: int, route_id: str, date: int, readingType: str, lat: int, long: int) -> None:
        super().__init__(id, route_id, date, readingType)

        self.lat: int = lat
        self.long: int = long
    
    def item_data(self):
        data = super().item_data()

        data[ReadingKeys.READING] = {
            PositionReadingKeys.LATITUDE: encode_float(self.lat),
            PositionReadingKeys.LONGITUDE: encode_float(self.long)
        }

        return data

    @classmethod
    def decode(cls, item: Dict[str, Any]):
        super().decode(item)

        item[ReadingKeys.READING][PositionReadingKeys.LATITUDE] = decode_float(item[ReadingKeys.READING][PositionReadingKeys.LATITUDE])
        item[ReadingKeys.READING][PositionReadingKeys.LONGITUDE] = decode_float(item[ReadingKeys.READING][PositionReadingKeys.LONGITUDE])

class PredictionReading(PositionReading):
    def __init__(
        self, id: int, 
        route_id: str, 
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
    
    @classmethod
    def decode(cls, item: Dict[str, Any]):
        super().decode(item)

        for k, v in item[ReadingKeys.READING].items():
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

READING_TYPE_MAP: Dict[str, AbstractReading] = {
    ReadingTypes.POSITIONAL: PositionReadingKeys,
    ReadingTypes.IMAGE: ImageReading,
    ReadingTypes.PREDICTION: PredictionReading,
    ReadingTypes.ANNOTATION: PredictionReading,
}

def decode_reading(reading_type, reading) -> None:
    READING_TYPE_MAP[reading_type].decode(reading)

def encode_reading(reading_type, reading) -> AbstractReading:
    if reading_type == ReadingTypes.POSITIONAL:
        return PositionReading(
            reading[ReadingKeys.READING_ID],
            reading[ReadingRouteKeys.ROUTE_ID],
            reading[ReadingKeys.TIMESTAMP],
            reading_type,
            reading[ReadingKeys.READING][PositionReadingKeys.LATITUDE],
            reading[ReadingKeys.READING][PositionReadingKeys.LONGITUDE],
        )
    elif reading_type == ReadingTypes.IMAGE:
        return ImageReading(
            reading[ReadingKeys.READING_ID],
            reading[ReadingRouteKeys.ROUTE_ID],
            reading[ReadingKeys.TIMESTAMP],
            reading_type,
            reading[ReadingKeys.READING][ImageReadingKeys.FILENAME],
        )
    elif reading_type in [ReadingTypes.PREDICTION, ReadingTypes.ANNOTATION]:
        binaries: Dict[str, bool] = {}

        reading_data = reading[ReadingKeys.READING]

        for key in CONDITION_BIARIES:
            if key in reading_data:
                binaries[key] = reading_data[key]

 
        confidences: Dict[str, float] = {}

        for key in CONDITION_CONFS:
            if key in reading_data:
                confidences[key] = reading_data[key]
 
        return PredictionReading(
            reading[ReadingKeys.READING_ID],
            reading[ReadingRouteKeys.ROUTE_ID],
            reading[ReadingKeys.TIMESTAMP],
            reading_type,
            reading_data[PositionReadingKeys.LATITUDE],
            reading_data[PositionReadingKeys.LONGITUDE],
            reading_data[ImageReadingKeys.FILENAME],
            binaries,
            confidences,
        )
    else:
        raise ValueError(f"unrecognized reading type {reading_type} for reading {reading}")