import copy
import time
from typing import Any, Dict, List
from readingdb.routestatus import RouteStatus
from readingdb.constants import *
from readingdb.reading import AbstractReading, ddb_to_dict

class Route():
    MAX_NAME_LENGTH = 21

    def __init__(
        self, 
        user_id: str, 
        id: str, 
        timestamp: int, 
        name: str=None, 
        sample_data: Dict[str, AbstractReading]=None
    ) -> None:
        '''sample_data contains a small collection of readings that belong to
        this route. Allows users to get an idea of what kind of data the route
        contains without loading all of it.
        '''

        self.user_id: str = user_id
        self.id: str = id
        self.name: str = name if name else id[:self.MAX_NAME_LENGTH]
        self.sample_data: Dict[str, AbstractReading] = copy.deepcopy(sample_data)  
        self.status = RouteStatus.UPLOADED
        self.timestamp: int = timestamp
        self.update_timestamp: int = int(time.time())

    @classmethod
    def decode_item(cls, item: Dict[str, Any]) -> None:
        if Constants.SAMPLE_DATA in item:
            for k, v in item[Constants.SAMPLE_DATA].items():
                ddb_to_dict(v)
                item[Constants.SAMPLE_DATA][k] = v
                
        item[Constants.STATUS] = int(item[Constants.STATUS])
        item[Constants.TIMESTAMP] = int(item[Constants.TIMESTAMP])
        if PredictionReadingKeys.ANNOTATION_TIMESTAMP in item:
            item[PredictionReadingKeys.ANNOTATION_TIMESTAMP] = int(item[PredictionReadingKeys.ANNOTATION_TIMESTAMP])

        if Constants.LAST_UPDATED in item:
            item[Constants.LAST_UPDATED] = int(item[Constants.LAST_UPDATED])
        else:
            item[Constants.LAST_UPDATED] = 0

        return item

    def item_data(self) -> Dict[str, Any]:
        data = {
            Constants.USER_ID: self.user_id,
            Constants.ROUTE_ID: self.id,
            Constants.STATUS: int(self.status),
            Constants.TIMESTAMP: self.timestamp,
            Constants.LAST_UPDATED: self.update_timestamp
        }

        if self.name:
            data[Constants.NAME] = self.name

        if self.sample_data:
            data[Constants.SAMPLE_DATA] = {} 
            for k, v in self.sample_data.items():
                data[Constants.SAMPLE_DATA][k] = v.item_data()

        return data