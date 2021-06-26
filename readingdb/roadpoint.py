from typing import Any, Dict
import readingdb.constants as C

class RoadPoint():
    Location = 'location'
    Latitude = 'latitude'
    Longitude = 'longitude'
    Idx = 'originalIndex'

    def __init__(self, point_data: Dict[str, Any]):
        self.lat = point_data[self.Location][self.Latitude] 
        self.lng = point_data[self.Location][self.Longitude]
        self.idx = point_data[self.Idx] if self.Idx in point_data else -1 

    def to_point(self):
        return {
            C.LAT: self.lat,
            C.LNG: self.lng
        }


    @property
    def has_idx(self) -> bool:
        return self.idx >= 0
         