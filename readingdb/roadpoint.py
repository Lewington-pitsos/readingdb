from typing import Any, Dict


class RoadPoint():
    Location = 'location'
    Latitude = 'latitude'
    Longitude = 'longitude'
    Idx = 'originalIndex'

    def __init__(self, point_data: Dict[str, Any]):
        self.lat = point_data[self.Location][self.Latitude] 
        self.lng = point_data[self.Location][self.Longitude]
        self.idx = point_data[self.Idx] if self.Idx in point_data else -1 
    
    @property
    def has_idx(self) -> bool:
        return self.idx >= 0
         