import copy
from pprint import pprint

from typing import Any, Dict
from readingdb.routestatus import RouteStatus
from readingdb.constants import *
from readingdb.reading import AbstractReading, ddb_to_dict, json_to_reading

class Route():
    def __init__(self, user_id: str, id: str, timestamp: int, name: str=None, sample_data: Dict[str, AbstractReading]=None) -> None:
        """sample_data contains a small collection of readings that belong to
        this route. Allows users to get an idea of what kind of data the route
        contains without loading all of it.
        """

        self.user_id: str = user_id
        self.id: str = id
        self.name: str = name
        self.sample_data: Dict[str, AbstractReading] = copy.deepcopy(sample_data)  
        self.status = RouteStatus.UPLOADED
        self.timestamp: int = timestamp

    @classmethod
    def decode_item(cls, item: Dict[str, Any]) -> None:
        if RouteKeys.SAMPLE_DATA in item:
            for k, v in item[RouteKeys.SAMPLE_DATA].items():
                ddb_to_dict(k, v)
                item[RouteKeys.SAMPLE_DATA][k] = v
                
        item[RouteKeys.STATUS] = int(item[RouteKeys.STATUS])
        item[RouteKeys.TIMESTAMP] = int(item[RouteKeys.TIMESTAMP])

    def item_data(self) ->  Dict[str, Any]:
        data = {
            RouteKeys.USER_ID: self.user_id,
            ReadingRouteKeys.ROUTE_ID: self.id,
            RouteKeys.STATUS: int(self.status),
            RouteKeys.TIMESTAMP: self.timestamp
        }

        if self.name:
            data[RouteKeys.NAME] = self.name

        if self.sample_data:
            data[RouteKeys.SAMPLE_DATA] = {} 
            for k, v in self.sample_data.items():
                data[RouteKeys.SAMPLE_DATA][k] = v.item_data()

        return data