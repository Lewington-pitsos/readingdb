from readingdb.rutils import RUtils
from typing import Any, Dict, List
from readingdb.constants import PositionReadingKeys, ReadingKeys

def interpolate_lat(p1, a1, p2, a2) -> float:
    return p1.lat * a1 + p2.lat * a2    

def interpolate_lng(p1, a1, p2, a2) -> float:
    return p1.lng * a1 + p2.lng * a2    

class LinePoint():
    @classmethod
    def from_reading(cls, entry: Dict[str, Any]):
        return LinePoint(
            RUtils.get_ts(entry),
            RUtils.get_lat(entry),
            RUtils.get_lng(entry),
        )
    
    @classmethod
    def from_point(cls, entry: Dict[str, Any]):
        return LinePoint(
            RUtils.get_ts(entry),
            entry[Constants.LATITUDE],
            entry[Constants.LONGITUDE],
        )

    def __init__(self, timestamp: int, lat: float, lng: float) -> None:
        self.timestamp = timestamp
        self.lat = lat
        self.lng = lng
    
    def __eq__(self, other)-> bool:
        return self.timestamp == other.timestamp and\
            self.lat == other.lat and\
            self.lng == other.lng

def linear_interp(prev: LinePoint, post: LinePoint, timestamp) -> LinePoint:
    time_dist = post.timestamp - prev.timestamp
    post_closeness = (timestamp - prev.timestamp) / time_dist
    prev_closeness = 1 - post_closeness   
    
    return  LinePoint(
        timestamp,
        interpolate_lat(
            prev, 
            prev_closeness, 
            post, 
            post_closeness
        ),
        interpolate_lng(
            prev, 
            prev_closeness, 
            post, 
            post_closeness
        )
    )

class LineRoute():
    @classmethod
    def from_readings(self, points: List[Dict[str, Any]], interp_alg=linear_interp):
        return LineRoute([LinePoint.from_reading(p) for p in points], interp_alg)

    def __init__(self, points: List[LinePoint], interp_alg=linear_interp):
        self.points = points
        self.interp_alg=interp_alg

    def contains(self, unix_time) -> bool:
        return not self.starts_after(unix_time) and not self.ends_before(unix_time)

    def ends_before(self, unix_time) -> bool:
        return unix_time > self.points[-1].timestamp
    
    def starts_after(self, unix_time) -> bool:
        return unix_time < self.points[0].timestamp
    
    def point_at(self, unix_time: int) -> LinePoint:
        if self.ends_before(unix_time):
            print(f"WARNING: cannot get position at a time {unix_time} from after the route finished {self.points[-1]}")
            return self.points[-1]
        if self.starts_after(unix_time):
            print(f"WARNING: cannot get position at {unix_time} a time from before the route began {self.points[0]}")
            return self.points[0]
            
        prev_point = self.points[0]
        next_point = None
        
        for p in self.points[1:]:
            if p.timestamp >= unix_time:
                next_point = p
                break
            else:
                prev_point = p
        
        return self.interp_alg(prev_point, next_point, unix_time)