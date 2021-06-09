import json
import copy
from readingdb.rutils import RUtils

import geopy.distance
from readingdb.roadpoint import RoadPoint
from readingdb.constants import ImageReadingKeys, PositionReadingKeys, ReadingKeys
import googlemaps
from readingdb.reading import PositionReading
from typing import Any, Dict, List, Tuple


class Geolocator():
    def __init__(self) -> None:
        with open('google/credentials.json') as f:
            credentials = json.load(f)

        self.gmaps = googlemaps.Client(key=credentials['key'])

    def geolocate(self, pos_readings: List[Dict[str, Any]]):
        road_points = self.__snapped_points(pos_readings)

        final_readings = []
        snapped_ids = []
        for p in road_points:
            if p.has_idx:
                snapped = self.__repositioned(pos_readings[p.idx], p)
                final_readings.append(snapped)
                snapped_ids.append(snapped[ReadingKeys.READING_ID])

        to_snap = [r for r in pos_readings if r[ReadingKeys.READING_ID] not in snapped_ids]
        for r in to_snap:
            p = self.__closest_point(r, road_points)
            final_readings.append(self.__repositioned(r, p))

        final_readings = sorted(final_readings, key=lambda r: RUtils.get_ts(r))

        return final_readings
    
    def __closest_point(self, reading: Dict[str, Any], road_points: List[RoadPoint]) -> RoadPoint:
        smallestDistance = 99999999999
        closestPoint = road_points[0]

        for p in road_points[1:]:
            dist = geopy.distance.geodesic(
                (RUtils.get_lat(reading), RUtils.get_lng(reading)), 
                (p.lat, p.lng)
            ).m
            if dist < smallestDistance:
                closestPoint = p
        return closestPoint


    def __repositioned(self, reading: Dict[str, Any], p: RoadPoint) -> None:
        repositioned = copy.deepcopy(reading)
        repositioned[ReadingKeys.READING][PositionReadingKeys.LATITUDE] = p.lat
        repositioned[ReadingKeys.READING][PositionReadingKeys.LONGITUDE] = p.lng
        return repositioned

    def __snapped_points(self, readings: List[Dict[str, Any]]):
        return [RoadPoint(p) for p in self.gmaps.snap_to_roads(
            [self.__to_latlng(p) for p in readings],
            interpolate=True
        )]
    def __to_latlng(self, reading: Dict[str, Any]) -> Tuple[float, float]:
        pos = reading[ReadingKeys.READING]

        return (pos[PositionReadingKeys.LATITUDE], pos[PositionReadingKeys.LONGITUDE])
        

    def generate_predictions(
        self, 
        pos_readings: List[Dict[str, Any]], 
        img_readings: List[Dict[str, Any]]
    ):
        snapped = self.geolocate(pos_readings)


        return img_readings
