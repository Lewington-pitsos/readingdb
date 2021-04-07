import abc
from os import read
from readingdb.s3uri import S3Uri
from typing import Any, Dict

from readingdb.constants import *
from readingdb.conditions import *
from readingdb.clean import encode_float, encode_bool, decode_bool, decode_float


class AbstractReading(abc.ABC):
    @abc.abstractmethod
    def item_data(self) -> Dict[str, Any]:
        raise NotImplementedError("not implemented")

    @abc.abstractclassmethod
    def decode(cls, item: Dict[str, Any]):
        raise NotImplementedError("not implemented")

class Reading(AbstractReading):
    def __init__(self, id: int, route_id: str, date: int, readingType: str) -> None:
        self.id: int = id
        self.route_id: str = route_id
        self.date: int = int(date) if isinstance(date, float) else date
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
    def __init__(self, id: int, route_id: int, date: int, readingType: str, url: str, uri: str = None) -> None:
        super().__init__(id, route_id, date, readingType)

        self.url: str = url
        self.uri = uri

    def item_data(self):
        data = super().item_data()

        data[ReadingKeys.READING] = {}

        self.add_file_data(data[ReadingKeys.READING])

        return data

    @classmethod
    def decode(cls, item: Dict[str, Any]):
        super().decode(item)
        pass

    def add_file_data(self, data):
        if self.url:
            data[ImageReadingKeys.FILENAME] = self.url

        if self.uri:
            data[ImageReadingKeys.URI] = {
                S3Path.BUCKET: self.uri.bucket,
                S3Path.KEY: self.uri.object_name
            }

    def set_uri(self, uri: S3Uri):
        self.uri: S3Uri = uri

    def has_uri(self) -> bool:
        return self.uri is not None

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

class PredictionReading(ImageReading, PositionReading):
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
        uri: str = None,
    ):
        PositionReading.__init__(self, id, route_id, date, readingType, lat, long)    

        self.url = url
        self.uri = uri
        self.predictionBinaries: Dict[str, bool] = predictionBinaries
        self.predictionConfidences: Dict[str, bool] = predictionConfidences
    
    @classmethod
    def decode(cls, item: Dict[str, Any]):
        PositionReading.decode(item)

        for k, v in item[ReadingKeys.READING].items():
            if k in CONDITION_BIARIES:
                item[ReadingKeys.READING][k] = decode_bool(v)
            if k in CONDITION_CONFS:
                item[ReadingKeys.READING][k] = decode_float(v)


    def item_data(self):
        data = PositionReading.item_data(self)


        self.add_file_data(data[ReadingKeys.READING])

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

def ddb_to_dict(reading_type, reading) -> None:
    READING_TYPE_MAP[reading_type].decode(reading)

def get_uri(reading_data: Dict[str, Any]) -> S3Uri:
    return None if not ImageReadingKeys.URI in reading_data else S3Uri.from_json(reading_data[ImageReadingKeys.URI])

def json_to_reading(reading_type: str, reading: Dict[str, Any]) -> AbstractReading:
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
            get_uri(reading[ReadingKeys.READING])
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
            get_uri(reading_data)
        )
    else:
        raise ValueError(f"unrecognized reading type {reading_type} for reading {reading}")