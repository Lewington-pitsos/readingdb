import abc
from os import read
from typing import Any, Dict, List
from readingdb.entity import Entity
from readingdb.s3uri import S3Uri
from readingdb.constants import *
from readingdb.entities import *
from readingdb.clean import encode_as_float, decode_bool, decode_float

class AbstractReading(abc.ABC):
    @abc.abstractmethod
    def item_data(self) -> Dict[str, Any]:
        raise NotImplementedError('not implemented')

    @abc.abstractclassmethod
    def decode(cls, item: Dict[str, Any]):
        raise NotImplementedError('not implemented')

class Reading(AbstractReading):
    def __init__(self, id: str, route_id: str, date: int, readingType: str) -> None:
        self.id: str = id
        self.route_id: str = route_id
        self.date: int = int(date) if isinstance(date, float) else date
        self.readingType: str = readingType
    def item_data(self):
        return {
            Constants.READING_ID: self.id,
            Constants.ROUTE_ID: self.route_id,
            Constants.TYPE: self.readingType,  
            Constants.TIMESTAMP: self.date, 
        }
    @classmethod
    def decode(cls, item: Dict[str, Any]):
        item[Constants.TIMESTAMP] = int(item[Constants.TIMESTAMP])

class ImageReading(Reading):
    def __init__(self, id: int, route_id: int, date: int, readingType: str, url: str = None, uri: str = None) -> None:
        super().__init__(id, route_id, date, readingType)

        if not url and not uri:
            raise ValueError('at least one of url or uri must be supplied when initializing an ImageReading')

        self.url: str = url
        self.uri = uri

    def item_data(self):
        data = super().item_data()
        data[Constants.READING] = {}
        self.add_file_data(data[Constants.READING])

        return data

    @classmethod
    def decode(cls, item: Dict[str, Any]):
        super().decode(item)
        pass

    def add_file_data(self, data):
        if self.url:
            data[Constants.FILENAME] = self.url

        if self.uri:
            data[Constants.URI] = {
                Constants.BUCKET: self.uri.bucket,
                Constants.KEY: self.uri.object_name
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

        data[Constants.READING] = {
            Constants.LATITUDE: encode_as_float(self.lat),
            Constants.LONGITUDE: encode_as_float(self.long)
        }

        return data

    @classmethod
    def decode(cls, item: Dict[str, Any]):
        super().decode(item)

        item[Constants.READING][Constants.LATITUDE] = decode_float(
            item[Constants.READING][Constants.LATITUDE]
        )
        item[Constants.READING][Constants.LONGITUDE] = decode_float(
            item[Constants.READING][Constants.LONGITUDE]
        )

class PredictionReading(ImageReading, PositionReading):
    def __init__(
        self, id: int, 
        route_id: str, 
        date: int, 
        readingType: str, 
        lat: int, 
        long: int,
        url: str,
        entities: List[Entity],
        annotation_timestamp: int,
        annotator_id: str,
        uri: str = None,
    ):
        PositionReading.__init__(self, id, route_id, date, readingType, lat, long)    
        
        self.url = url
        self.uri = uri
        self.entites: List[Entity] = entities
        self.annotator_id = annotator_id
        self.annotation_timestamp = annotation_timestamp
    
    @classmethod
    def decode(cls, item: Dict[str, Any]):
        PositionReading.decode(item)

        for e in item[Constants.READING][PredictionReadingKeys.ENTITIES]:
            e[Constants.CONFIDENCE] = decode_float(e[Constants.CONFIDENCE])
            e[Constants.PRESENT] = decode_bool(e[Constants.PRESENT])
            e[Constants.SEVERITY] = decode_float(e[Constants.SEVERITY]) if Constants.SEVERITY in e else 1.0
        
        item[PredictionReadingKeys.ANNOTATION_TIMESTAMP] = int(item[PredictionReadingKeys.ANNOTATION_TIMESTAMP])
            
    def item_data(self):
        data = PositionReading.item_data(self)
        self.add_file_data(data[Constants.READING])

        encoded_entities = []
        for e in self.entites:
            encoded_entities.append(e.encode())
        data[Constants.READING][PredictionReadingKeys.ENTITIES] = encoded_entities

        data[PredictionReadingKeys.ANNOTATOR_ID] = self.annotator_id
        data[PredictionReadingKeys.ANNOTATION_TIMESTAMP] = int(self.annotation_timestamp)

        return data

READING_TYPE_MAP: Dict[str, AbstractReading] = {
    Constants.POSITIONAL: PositionReading,
    Constants.IMAGE: ImageReading,
    Constants.PREDICTION: PredictionReading,
}

def ddb_to_dict(reading) -> None:
    reading_type = reading[Constants.TYPE]
    READING_TYPE_MAP[reading_type].decode(reading)

def get_uri(reading_data: Dict[str, Any]) -> S3Uri:
    return None if not Constants.URI in reading_data else S3Uri.from_json(reading_data[Constants.URI])

def get_filename(reading_data: Dict[str, Any]) -> S3Uri:
    return None if not Constants.FILENAME in reading_data else reading_data[Constants.FILENAME]
    
def json_to_reading(reading_type: str, reading: Dict[str, Any]) -> Reading:
    if reading_type == Constants.POSITIONAL:
        return PositionReading(
            reading[Constants.READING_ID],
            reading[Constants.ROUTE_ID],
            reading[Constants.TIMESTAMP],
            reading_type,
            reading[Constants.READING][Constants.LATITUDE],
            reading[Constants.READING][Constants.LONGITUDE],
        )
    elif reading_type == Constants.IMAGE:
        return ImageReading(
            reading[Constants.READING_ID],
            reading[Constants.ROUTE_ID],
            reading[Constants.TIMESTAMP],
            reading_type,
            get_filename(reading[Constants.READING]),
            get_uri(reading[Constants.READING])
        )
    elif reading_type in [Constants.PREDICTION]:
        binaries: Dict[str, bool] = {}
        reading_data = reading[Constants.READING]

        for key in ENTITY_BIARIES:
            if key in reading_data:
                binaries[key] = reading_data[key]
        
        entities = []
        
        for e in reading_data[PredictionReadingKeys.ENTITIES]:
            entities.append(Entity(
                e[Constants.NAME],
                e[Constants.CONFIDENCE], 
                e[Constants.PRESENT],
                e[Constants.SEVERITY] if Constants.SEVERITY in e else 1.0
            ))

        return PredictionReading(
            reading[Constants.READING_ID],
            reading[Constants.ROUTE_ID],
            reading[Constants.TIMESTAMP],
            reading_type,
            reading_data[Constants.LATITUDE],
            reading_data[Constants.LONGITUDE],
            get_filename(reading_data),
            entities,
            annotation_timestamp=reading[PredictionReadingKeys.ANNOTATION_TIMESTAMP],
            annotator_id=reading[PredictionReadingKeys.ANNOTATOR_ID],
            uri=get_uri(reading_data)
        )
    else:
        raise ValueError(f'unrecognized reading type {reading_type} for reading {reading}')