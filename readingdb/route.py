import copy
from readingdb.format import route_sort_key
import time
from typing import Any, Dict, List
from readingdb.routestatus import RouteStatus
from readingdb.constants import *
from readingdb.reading import Reading

class Route():
    MAX_NAME_LENGTH = 21

    def __init__(
        self, 
        user_id: str, 
        group_id: str,
        id: str, 
        timestamp: int, 
        name: str=None, 
        geohashes: List[str] = [],
        sample_data: Dict[str, Reading]=None,
        layer_id: str = None
    ) -> None:
        '''sample_data contains a small collection of readings that belong to
        this route. Allows users to get an idea of what kind of data the route
        contains without loading all of it.
        '''

        self.user_id: str = user_id
        self.id: str = id
        self.name: str = name if name else id[:self.MAX_NAME_LENGTH]
        self.sample_data: Dict[str, Reading] = copy.deepcopy(sample_data)  
        self.status = RouteStatus.UPLOADED
        self.timestamp: int = timestamp
        self.update_timestamp: int = int(time.time())
        self.geohashes = geohashes
        self.group_id = group_id
        self.layer_id = layer_id

    @classmethod
    def decode_item(cls, item: Dict[str, Any]) -> None:
        if Constants.SAMPLE_DATA in item:
            for k, v in item[Constants.SAMPLE_DATA].items():
                Reading.decode(v)
                item[Constants.SAMPLE_DATA][k] = v
                
        item[Constants.STATUS] = int(item[Constants.STATUS])
        item[Constants.TIMESTAMP] = int(item[Constants.TIMESTAMP])
        if Constants.ANNOTATION_TIMESTAMP in item:
            item[Constants.ANNOTATION_TIMESTAMP] = int(item[Constants.ANNOTATION_TIMESTAMP])

        if Constants.LAST_UPDATED in item:
            item[Constants.LAST_UPDATED] = int(item[Constants.LAST_UPDATED])
        else:
            item[Constants.LAST_UPDATED] = 0

        return item

    def item_data(self) -> Dict[str, Any]:
        data = {
            Constants.PARTITION_KEY: Constants.ROUTE_PK,
            Constants.SORT_KEY: route_sort_key(self.id),
            Constants.ROUTE_ID: self.id,
            Constants.STATUS: int(self.status),
            Constants.TIMESTAMP: self.timestamp,
            Constants.LAST_UPDATED: self.update_timestamp,
            Constants.ROUTE_HASHES: self.geohashes,
            Constants.GROUP_ID: self.group_id
        }

        if self.layer_id:
            data[Constants.LAYER_ID] = self.layer_id

        if self.name:
            data[Constants.NAME] = self.name

        if self.sample_data:
            data[Constants.SAMPLE_DATA] = {} 
            for k, v in self.sample_data.items():
                data[Constants.SAMPLE_DATA][k] = v.item_data()

        return data