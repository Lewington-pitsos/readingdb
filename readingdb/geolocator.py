import time
import json
import copy

import haversine as hs
import readingdb.constants as C
from haversine import Unit
from readingdb.lineroute import LineRoute
from readingdb.rutils import RUtils
from readingdb.roadpoint import RoadPoint
from readingdb.constants import PredictionReadingKeys, FAUX_ANNOTATOR_ID, ImageReadingKeys, PositionReadingKeys, PredictionReadingKeys, ReadingKeys, ReadingTypes, S3Path
import googlemaps
from typing import Any, Dict, List, Tuple

class Geolocator():
    def __init__(self, overlap: int = 15) -> None:
        with open('google/credentials.json') as f:
            credentials = json.load(f)

        self.gmaps = googlemaps.Client(key=credentials['key'])
        self.overlap = overlap
        self.max_points = 100

    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------ FILTERING --------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    def filter_stationary(self, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        keep = [readings[0]]
        dropMillis = 5000
        gpsErrMeters = 8
        lastMotion = readings[0]

        buffer = []
        
        readings = sorted(readings, key=lambda r: r[ReadingKeys.TIMESTAMP])

        for r in readings[1:]:
            if self.__meters_dist(r, lastMotion) > gpsErrMeters:
                keep.extend(buffer)
                buffer = []
                keep.append(r)
                lastMotion = r
            elif self.__milli_diff(r, lastMotion) < dropMillis:
                keep.append(r)
            else:
                buffer.append(r)

                if len(buffer) > 10:
                    buffer.pop(0)

        return keep

    def wanted_img_readings(
        self,
        pos_readings: List[Dict[str, Any]], 
        img_readings: List[Dict[str, Any]] 
    ):
        interpolated = self.interpolated(pos_readings, img_readings)
        filtered = self.filter_stationary(interpolated)

        wanted_images = set()

        for f in filtered:
            wanted_images.add(f[ReadingKeys.READING][ImageReadingKeys.URI][S3Path.KEY])
        
        return [i for i in img_readings if i[ReadingKeys.READING][ImageReadingKeys.URI][S3Path.KEY] in wanted_images]

    def __milli_diff(self, r1: Dict[str, Any], r2: Dict[str, Any]) -> int:
        return r1[ReadingKeys.TIMESTAMP] - r2[ReadingKeys.TIMESTAMP] 

    def __meters_dist(self, r1: Dict[str, Any], r2: Dict[str, Any]) -> int:
        p1 = self.__to_point(r1)
        p2 = self.__to_point(r2)

        return hs.haversine(p1, p2, unit=Unit.METERS)

    def __to_point(self, r1: Dict[str, Any]) -> Tuple[float, float]:
        reading = r1[ReadingKeys.READING]
        return (reading[PositionReadingKeys.LATITUDE], reading[PositionReadingKeys.LONGITUDE])
        
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------ SNAPPING --------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------
    # ------------------------------------------------------------------------

    def geolocate(self, pos_readings: List[Dict[str, Any]], replacement=False):
        if len(pos_readings) == 0:
            return []

        if len(pos_readings) < self.overlap:
            return pos_readings

        all_final_readings = []

        start_idx = 0
        while start_idx < len(pos_readings):
            end_idx = start_idx + self.max_points
            overlap = self.overlap if end_idx < len(pos_readings) else 0
            next_readings = pos_readings[start_idx:end_idx]

            snapped = self.__geolocate_subset(next_readings, replacement)
            if replacement:
                all_final_readings.extend(self.__filter_duplicates(all_final_readings, snapped))
            else:
                all_final_readings.extend(snapped[min(self.overlap, start_idx):])
            start_idx += self.max_points - overlap

        return all_final_readings

    def __filter_duplicates(self, current_points, new_points):
        to_add = []
        for p in new_points:
            lat = p[C.LAT]
            lng = p[C.LNG]
            for cp in current_points:
                if cp[C.LAT] == lat and cp[C.LNG] == lng:
                    break
            else:
                to_add.append(p)
        return to_add

    def __geolocate_subset(self, pos_readings: List[Dict[str, Any]], replace=False):
        if replace:
            return [r.to_point() for r in  self.__snapped_points(pos_readings)]
        return self.__snap_readings(pos_readings)

    def __snap_readings(self, pos_readings: List[Dict[str, Any]]):
        road_points = self.__snapped_points(pos_readings)

        final_readings = []
        for p in road_points:
            if p.has_idx:
                snapped = self.__repositioned(pos_readings[p.idx], p)
                final_readings.append(snapped)

        return sorted(final_readings, key=lambda r: RUtils.get_ts(r))

    def __repositioned(self, reading: Dict[str, Any], p: RoadPoint) -> None:
        repositioned = copy.deepcopy(reading)
        repositioned[ReadingKeys.READING][PositionReadingKeys.LATITUDE] = p.lat
        repositioned[ReadingKeys.READING][PositionReadingKeys.LONGITUDE] = p.lng
        repositioned[ReadingKeys.READING][PositionReadingKeys.PLACE_ID] = p.placeID
        return repositioned

    def __snapped_points(self, readings: List[Dict[str, Any]]):
        return [RoadPoint(p) for p in self.gmaps.snap_to_roads(
            [self.__to_latlng(p) for p in readings],
            interpolate=True
        )]

    def __to_latlng(self, reading: Dict[str, Any]) -> Tuple[float, float]:
        if ReadingKeys.READING in reading:
            pos = reading[ReadingKeys.READING]

            return (pos[PositionReadingKeys.LATITUDE], pos[PositionReadingKeys.LONGITUDE])
        
        return (reading[C.LAT], reading[C.LNG])

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
        img_readings = self.wanted_img_readings(pos_readings, img_readings)
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
        pred_reading[PredictionReadingKeys.ANNOTATOR_ID] = FAUX_ANNOTATOR_ID
        pred_reading[ReadingKeys.READING][PositionReadingKeys.LATITUDE] = point.lat
        pred_reading[ReadingKeys.READING][PositionReadingKeys.LONGITUDE] = point.lng

        if ImageReadingKeys.URI in img_reading[ReadingKeys.READING]:
            pred_reading[ReadingKeys.READING][ImageReadingKeys.URI] = RUtils.get_uri(img_reading)
        if ImageReadingKeys.FILENAME in img_reading[ReadingKeys.READING]:
            pred_reading[ReadingKeys.READING][ImageReadingKeys.FILENAME] = RUtils.get_filename(img_reading)
        else:
            pred_reading[ReadingKeys.READING][ImageReadingKeys.FILENAME] = ""

        return pred_reading