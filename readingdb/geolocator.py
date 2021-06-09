import time
import json
import copy
from readingdb.lineroute import LineRoute
from readingdb.rutils import RUtils

import geopy.distance
from readingdb.roadpoint import RoadPoint
from readingdb.constants import AnnotatorKeys, FAUX_ANNOTATOR_ID, ImageReadingKeys, PositionReadingKeys, PredictionReadingKeys, ReadingKeys, ReadingTypes
import googlemaps
from typing import Any, Dict, List, Tuple


class Geolocator():
    def __init__(self) -> None:
        with open('google/credentials.json') as f:
            credentials = json.load(f)

        self.gmaps = googlemaps.Client(key=credentials['key'])

    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------ SNAPPING --------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    def geolocate(self, pos_readings: List[Dict[str, Any]]):
        if len(pos_readings) == 0:
            return []

        required_cnt = len(pos_readings)
        all_final_readings = []

        while len(all_final_readings) < required_cnt:
            snapped_cnt = len(all_final_readings)
            next_readings = pos_readings[snapped_cnt:snapped_cnt+100]
            all_final_readings.extend(self.__geolocate_subset(next_readings))
        
        return all_final_readings

    def __geolocate_subset(self, pos_readings: List[Dict[str, Any]]):
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

    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------ INTERPOLATING ---------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    def generate_predictions(
        self, 
        pos_readings: List[Dict[str, Any]], 
        img_readings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        snapped = self.geolocate(pos_readings)
        return self.interpolated(snapped, img_readings)

    def interpolated(
        self, 
        pos_readings: List[Dict[str, Any]], 
        img_readings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        lr = LineRoute.from_readings(pos_readings)

        pred_readings = []
        for r in img_readings:
            ts = RUtils.get_ts(r)
            if lr.contains(ts):
                point = lr.point_at(ts)
                pred_readings.append(self.__prediction_reading(r, point))

        return pred_readings

    def __prediction_reading(self, img_reading: Dict[str, Any], point: Dict[str, Any]) -> Dict[str, Any]:
        pred_reading = copy.deepcopy(img_reading)
        pred_reading[ReadingKeys.TYPE] = ReadingTypes.PREDICTION
        pred_reading[ReadingKeys.READING][PredictionReadingKeys.ENTITIES] = []
        pred_reading[PredictionReadingKeys.ANNOTATION_TIMESTAMP] = int(time.time() * 1000)
        pred_reading[AnnotatorKeys.ANNOTATOR_ID] = FAUX_ANNOTATOR_ID
        pred_reading[ReadingKeys.READING][PositionReadingKeys.LATITUDE] = point.lat
        pred_reading[ReadingKeys.READING][PositionReadingKeys.LONGITUDE] = point.lng

        if ImageReadingKeys.URI in img_reading[ReadingKeys.READING]:
                pred_reading[ReadingKeys.READING][ImageReadingKeys.URI] = RUtils.get_uri(img_reading)
        if ImageReadingKeys.FILENAME in img_reading[ReadingKeys.READING]:
                pred_reading[ReadingKeys.READING][ImageReadingKeys.FILENAME] = RUtils.get_filename(img_reading)

        return pred_reading