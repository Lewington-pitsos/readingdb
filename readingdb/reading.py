from typing import Any, Dict, List
import pygeohash as pgh

from readingdb.entity import Entity
from readingdb.s3uri import S3Uri
from readingdb.constants import *
from readingdb.entities import *
from readingdb.clean import encode_as_float, decode_bool, decode_float

def reading_sort_key(layer_id:str, reading_id: str) -> str:
    return f'{layer_id}#{reading_id}'

class Reading():
    def __init__(
        self, 
        id: str, 
        route_id: str, 
        date: int, 
        readingType: str,
        lat: int, 
        lng: int,
        layer_id: str = DEFAULT_LAYER_ID
    ) -> None:
        self.id: str = id
        self.route_id: str = route_id
        self.date: int = int(date) if isinstance(date, float) else date
        self.readingType: str = readingType
        self.lat: int = lat
        self.lng: int = lng
        self.layer_id = layer_id

    def item_data(self):
        return {
            Constants.PART_KEY: self.geohash(),
            Constants.SORT_KEY: self.sort_key(),
            Constants.ROUTE_ID: self.route_id,
            Constants.TYPE: self.readingType,  
            Constants.TIMESTAMP: self.date, 
            Constants.READING: {
                Constants.LATITUDE: encode_as_float(self.lat),
                Constants.LONGITUDE: encode_as_float(self.lng),
            }
        }

    def sort_key(self) -> str:
        return reading_sort_key(self.layer_id, self.id)
    def geohash(self) -> str:
        return pgh.encode(self.lat, self.lng, precision=GEOHASH_PRECISION)

    @classmethod
    def decode(cls, item: Dict[str, Any]):
        item[Constants.GEOHASH] = item[Constants.PART_KEY]

        sort_key_segments = item[Constants.SORT_KEY].split('#')
        item[Constants.LAYER_ID] = sort_key_segments[0]
        item[Constants.READING_ID] = sort_key_segments[1]

        item[Constants.TIMESTAMP] = int(item[Constants.TIMESTAMP])



class PredictionReading(Reading):
    def __init__(
        self, id: int, 
        route_id: str, 
        date: int, 
        readingType: str, 
        lat: int, 
        lng: int,
        url: str,
        entities: List[Entity],
        annotation_timestamp: int,
        annotator_id: str,
        uri: str = None,
    ):
        super().__init__(id, route_id, date, readingType, lat, lng)

        self.url = url
        self.uri = uri
        self.entites: List[Entity] = entities
        self.annotator_id = annotator_id
        self.annotation_timestamp = annotation_timestamp
    
    @classmethod
    def decode(cls, item: Dict[str, Any]):
        super().decode(item)
        item[Constants.READING][Constants.LATITUDE] = decode_float(
            item[Constants.READING][Constants.LATITUDE]
        )
        item[Constants.READING][Constants.LONGITUDE] = decode_float(
            item[Constants.READING][Constants.LONGITUDE]
        )

        for e in item[Constants.READING][Constants.ENTITIES]:
            e[Constants.CONFIDENCE] = decode_float(e[Constants.CONFIDENCE])
            e[Constants.PRESENT] = decode_bool(e[Constants.PRESENT])
            e[Constants.SEVERITY] = decode_float(e[Constants.SEVERITY]) if Constants.SEVERITY in e else 1.0
        
        item[Constants.ANNOTATION_TIMESTAMP] = int(item[Constants.ANNOTATION_TIMESTAMP])
            
    def item_data(self):
        data = super().item_data()
        self.__add_file_data(data[Constants.READING])

        encoded_entities = []
        for e in self.entites:
            encoded_entities.append(e.encode())
        data[Constants.READING][Constants.ENTITIES] = encoded_entities

        data[Constants.ANNOTATOR_ID] = self.annotator_id
        data[Constants.ANNOTATION_TIMESTAMP] = int(self.annotation_timestamp)

        return data

    def set_uri(self, uri: S3Uri):
        self.uri: S3Uri = uri

    def has_uri(self) -> bool:
        return self.uri is not None

    def __add_file_data(self, data):
        if self.url:
            data[Constants.FILENAME] = self.url

        if self.uri:
            data[Constants.URI] = {
                Constants.BUCKET: self.uri.bucket,
                Constants.KEY: self.uri.object_name
            }

READING_TYPE_MAP: Dict[str, PredictionReading] = {
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
    if reading_type in [Constants.PREDICTION]:
        binaries: Dict[str, bool] = {}
        reading_data = reading[Constants.READING]

        for key in ENTITY_BIARIES:
            if key in reading_data:
                binaries[key] = reading_data[key]
        
        entities = []
        
        for e in reading_data[Constants.ENTITIES]:
            entities.append(Entity(
                e[Constants.ENTITY_NAME],
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
            annotation_timestamp=reading[Constants.ANNOTATION_TIMESTAMP],
            annotator_id=reading[Constants.ANNOTATOR_ID],
            uri=get_uri(reading_data)
        )
    else:
        raise ValueError(f'unrecognized reading type {reading_type} for reading {reading}')