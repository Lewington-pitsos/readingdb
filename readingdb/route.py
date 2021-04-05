import copy

from typing import Any, Dict
from readingdb.routestatus import RouteStatus
from readingdb.constants import *
from readingdb.reading import AbstractReading, decode_reading, encode_reading

class Route():
    def __init__(self, user_id: str, id: str, name: str=None, sample_data: Dict[str, AbstractReading]=None) -> None:
        """sample_data contains a small collection of readings that belong to
        this route. Allows users to get an idea of what kind of data the route
        contains without loading all of it.
        """

        self.user_id: str = user_id
        self.id: str = id
        self.name: str = name
        self.sample_data: Dict[str, AbstractReading] = copy.deepcopy(sample_data)  
        self.status = RouteStatus.UPLOADED

        if self.sample_data:
            for k, v in self.sample_data.items():
                self.sample_data[k] = encode_reading(k, v)

    @classmethod
    def decode_item(self, item: Dict[str, Any]) -> None:
        if RouteKeys.SAMPLE_DATA in item:
            for k, v in item[RouteKeys.SAMPLE_DATA].items():
                decode_reading(k, v)
                item[RouteKeys.SAMPLE_DATA][k] = v

    def item_data(self) ->  Dict[str, Any]:
        data = {
            RouteKeys.USER_ID: self.user_id,
            ReadingRouteKeys.ROUTE_ID: self.id,
        }

        if self.name:
            data[RouteKeys.NAME] = self.name

        if self.sample_data:
            data[RouteKeys.SAMPLE_DATA] = {} 
            for k, v in self.sample_data.items():
                data[RouteKeys.SAMPLE_DATA][k] = v.item_data()

        return data