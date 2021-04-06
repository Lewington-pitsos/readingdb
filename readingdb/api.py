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

from boto3.dynamodb.conditions import Key

from readingdb.db import DB
from readingdb.normalize import *
from readingdb.constants import *

class API(DB, ReadingDB):
    def __init__(
        self, 
        url, 
        resource_name='dynamodb', 
        bucket="mobileappsessions172800-main",
        config=None
    ):
        super().__init__(url=url, resource_name=resource_name, config=config)
        self.bucket = bucket

        self.s3_client = boto3.client('s3', config=config)

    def upload(self, route_spec: RouteSpec, user_id: str) -> Route:
        route_key = self.__generate_route_id()
        route_id = str(time.time()) + "-" + route_key

        print(f"uploading route {route_spec} as {route_id}")

        initial_entries = {}

        for reading_spec in route_spec.reading_specs:
            print(f"starting upload for reading {reading_spec}")

            entries = reading_spec.load_readings()   

            if len(entries) > 0:
                finalized_entries = self.__save_entries(route_id, reading_spec.reading_type, entries)
                initial_entries[reading_spec.reading_type] = finalized_entries[0]

                print("Finished saving all readings to FDS database")
            else:
                print(f"No entries found for reading specification {reading_spec}")

        route = Route(
            user_id,
            route_id,
            route_spec.name if route_spec.name else route_key,
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

    def __upload_file(self, route_id, file_name, bucket):
        object_name = route_id + file_name        
        response = self.s3_client.upload_file(file_name, bucket, object_name)

        return response, object_name

    def __save_entry(self, entry: Reading) -> AbstractReading:
        if entry.readingType in ReadingTypes.IMAGE_TYPES:
            return self.__save_img_entry(entry)

        self.put_reading(entry)
        return entry

    def __save_img_entry(self, entry: ImageReading) -> AbstractReading:
        if not entry.has_uri():
            _, object_name = self.__upload_file(
                entry.route_id, 
                entry.url, 
                self.bucket
            )

            entry.set_uri(S3Uri(
                self.bucket,
                object_name,
            ))

        self.put_reading(entry)

        return entry

    def __generate_route_id(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))

    def __save_entries(self, route_id, entry_type, entries) -> List[AbstractReading]:
        print("uploading entries")
        finalized: List[AbstractReading] = []
        for i, e in enumerate(tqdm(entries)):
            e[ReadingKeys.READING_ID] = i
            e[ReadingRouteKeys.ROUTE_ID] = route_id
            e = json_to_reading(entry_type, e)
            e = self.__save_entry(e)
            finalized.append(e)

        return finalized