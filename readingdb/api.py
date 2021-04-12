from botocore.utils import parse_timestamp
from readingdb.readingdb import ReadingDB
from readingdb.routestatus import RouteStatus
from typing import Any, Dict, List
from readingdb.s3uri import S3Uri
from readingdb.route import Route
from readingdb.reading import AbstractReading, ImageReading, Reading, json_to_reading
from readingdb.routespec import RouteSpec
import boto3
import time
import random
import string
from tqdm import tqdm
import uuid

from boto3.dynamodb.conditions import Key

from readingdb.db import DB
from readingdb.constants import *

class API(DB, ReadingDB):
    def __init__(
        self, 
        url, 
        resource_name='dynamodb', 
        bucket="mobileappsessions172800-main",
        region_name="ap-southeast-2",
        config=None
    ):
        super().__init__(url=url, resource_name=resource_name, region_name=region_name, config=config)
        self.bucket = bucket

        self.s3_client = boto3.client('s3', region_name=region_name, config=config)

    def save_route(self, route_spec: RouteSpec, user_id: str) -> Route:
        route_id = str(uuid.uuid1())

        print(f"uploading route {route_spec} as {route_id}")

        initial_entries = {}
        timestamp = 0

        for reading_spec in route_spec.reading_specs:
            print(f"starting upload for reading {reading_spec}")

            entries = reading_spec.load_readings()   

            if len(entries) > 0:
                finalized_entries = self.__save_entries(route_id, reading_spec.reading_type, entries)
                first_entry: Reading = finalized_entries[0]
                initial_entries[reading_spec.reading_type] = first_entry

                if timestamp == 0:
                    timestamp = first_entry.date

                print("Finished saving all readings to FDS database")
            else:
                print(f"No entries found for reading specification {reading_spec}")

        route = Route(
            user_id,
            route_id,
            timestamp,
            route_spec.name if route_spec.name else None,
            initial_entries
        )

        self.put_route(route)
        print(f"Finished uploading route {route_id} for user {user_id}")

        return route

    def save_predictions(self, readings: List[Dict[str, Any]], route_id: int, user_id: str) -> None:
        self.__save_entries(route_id, ReadingTypes.PREDICTION, readings)

        self.set_route_status(route_id, user_id, RouteStatus.COMPLETE)

    def set_as_predicting(self, route_id: str, user_id: str) -> None:
        self.set_route_status(route_id, user_id, RouteStatus.PREDICTING)

    def all_route_readings(self, route_id: str) -> List[Dict[str, Any]]:
        readings = super().all_route_readings(route_id)

        self.__inject_presigned_urls(readings)

        return readings

    def routes_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        routes = super().routes_for_user(user_id)
        for r in routes:
            self.__inject_samples_with_presigned_urls(r)
        
        return routes

    def get_route(self, route_id: str, user_id: str) -> Dict[str, Any]:
        r = super().get_route(route_id, user_id)
        if not r:
            return r

        self.__inject_samples_with_presigned_urls(r)

        return r
    
    def __inject_samples_with_presigned_urls(self, route: Dict[str, Any]) -> None:
        if RouteKeys.SAMPLE_DATA in route:
            for _, sample in route[RouteKeys.SAMPLE_DATA].items():
                self.__inject_presigned_url(sample)

    def __inject_presigned_urls(self, readings: List[Dict[str, Any]]) -> None:
        for r in readings:
            self.__inject_presigned_url(r)
    
    def __inject_presigned_url(self, r: Dict[str, Any]) -> None:    
        if ImageReadingKeys.URI in r[ReadingKeys.READING]:
            uri = r[ReadingKeys.READING][ImageReadingKeys.URI]

            r[ReadingKeys.READING][ImageReadingKeys.PRESIGNED_URL] = self.__presigned_url(
                uri[S3Path.BUCKET],
                uri[S3Path.KEY],
            )

    def __presigned_url(self, bucket: str, object: str) -> str:
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket,'Key': object},
            ExpiresIn=259200
        )

    def __upload_file(self, route_id, file_name, bucket):
        object_name = route_id + file_name        
        response = self.s3_client.upload_file(file_name, bucket, object_name)

        return response, object_name

    def __save_entry(self, entry: Reading) -> AbstractReading:
        if entry.readingType in ReadingTypes.IMAGE_TYPES:
            return self.__save_img_entry(entry)

        self.put_reading(entry)
        return entry

    def __upload_entry_file(self, entry) -> S3Uri:
        _, object_name = self.__upload_file(
                entry.route_id, 
                entry.url, 
                self.bucket
            )

        return S3Uri(
            self.bucket,
            object_name,
        )

    def __save_img_entry(self, entry: ImageReading) -> AbstractReading:
        if not entry.has_uri():
            uri: S3Uri = self.__upload_entry_file(entry)
            entry.set_uri(uri)

        self.put_reading(entry)

        return entry

    def __generate_route_id(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))

    def __json_to_entry(self, e: Dict[str, Any], entry_type: str, reading_id: str, route_id: str) -> Reading:
        e[ReadingKeys.READING_ID] = reading_id
        e[ReadingRouteKeys.ROUTE_ID] = route_id
        return json_to_reading(entry_type, e)

    def __save_entries(self, route_id, entry_type, entries) -> List[AbstractReading]:
        finalized: List[AbstractReading] = []
        for e in tqdm(entries):
            e = self.__json_to_entry(e, entry_type, str(uuid.uuid1()), route_id)
            e = self.__save_entry(e)
            finalized.append(e)

        return finalized