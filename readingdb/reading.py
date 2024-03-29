from typing import Any, Dict, List
import pygeohash as pgh

from readingdb.entity import Entity
from readingdb.s3uri import S3Uri
from readingdb.constants import *
from readingdb.entities import *
from readingdb.clean import encode_as_float, decode_bool, decode_float

def reading_sort_key(reading_type: str, reading_id: str) -> str:
    return f'{reading_type}#{reading_id}'

def get_geohash(lat: float, lng: float) -> str:
    return pgh.encode(lat, lng, precision=GEOHASH_PRECISION)

def reading_partition_key(lat: str, lng: str, reading_type: str) -> str:
    geohash = get_geohash(lat, lng)
    return geohash_partition_key(geohash, reading_type)

def geohash_partition_key(geohash: str, reading_type: str) -> str:
    return f'{geohash}#{reading_type}' 

#TODO: ask louka about the route id and if that is a necessary attribute
class Reading():
    def __init__(
        self, id: int, 
        route_id: str, 
        timestamp: int, 
        readingType: str, 
        lat: int, 
        lng: int,
        url: str,
        entities: List[Entity],
        annotation_timestamp: int,
        annotator_id: str,
        uri: str = None,
    ):
        self.id: str = id
        self.route_id: str = route_id
        self.timestamp: int = int(timestamp) if isinstance(timestamp, float) else timestamp
        self.reading_type: str = readingType
        self.lat: int = lat
        self.lng: int = lng
        self.geohash = get_geohash(lat, lng)
        self.url = url
        self.uri = uri
        self.entites: List[Entity] = entities
        self.annotator_id = annotator_id
        self.annotation_timestamp = annotation_timestamp
        
        self.data: Dict = {
            Constants.LATITUDE: lat,
            Constants.LONGITUDE: lng,
            Constants.ENTITIES: entities,
            Constants.URI: uri
        }
    
    @classmethod
    def decode(cls, item: Dict[str, Any]):
        item[Constants.TIMESTAMP] = int(item[Constants.TIMESTAMP])
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

    @staticmethod
    def get_key(reading: Dict[str, Any]) -> Dict[str, str]:
        return {
            Constants.PARTITION_KEY: reading_partition_key(
                reading[Constants.READING][Constants.LATITUDE],
                reading[Constants.READING][Constants.LONGITUDE],
                reading[Constants.READING_TYPE]
            ),
            Constants.SORT_KEY: reading[Constants.READING_ID]
        }

    def item_data(self):
        data = {
            Constants.PARTITION_KEY: reading_partition_key(self.lat, self.lng, self.reading_type),
            Constants.SORT_KEY: self.id,
            Constants.GEOHASH: self.geohash,
            Constants.ROUTE_ID: self.route_id,
            Constants.READING_ID: self.id,
            Constants.READING_TYPE: self.reading_type,  
            Constants.TIMESTAMP: self.timestamp, 
            Constants.READING: {
                Constants.LATITUDE: encode_as_float(self.lat),
                Constants.LONGITUDE: encode_as_float(self.lng),
            }
        }
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

    def query_data(self) -> Dict[str, str]:
        return {
            Constants.READING_TYPE: self.reading_type,
            Constants.READING_ID: self.id,
            Constants.GEOHASH: self.geohash
        }

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

        return Reading(
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