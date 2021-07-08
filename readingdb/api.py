from collections import defaultdict
import json
import sys
from readingdb.readingdb import ReadingDB
from readingdb.routestatus import RouteStatus
from typing import Any, Dict, List, Tuple
from readingdb.s3uri import S3Uri
from readingdb.route import Route
from readingdb.reading import AbstractReading, ImageReading, Reading, json_to_reading
from readingdb.routespec import RouteSpec
import boto3
import uuid

from readingdb.db import DB
from readingdb.endpoints import LAMBDA_ENDPOINT
from readingdb.constants import *

class API(DB, ReadingDB):
    ECS_TASKS_KEY = 'tasks'

    def __init__(
        self, 
        url, 
        resource_name='dynamodb', 
        tmp_bucket='mobileappsessions172800-main',
        bucket='mobileappsessions172800-main',
        region_name='ap-southeast-2',
        config=None,
        size_limit=999999999999999
        # size_limit=2_500_000
    ):
        super().__init__(url=url, resource_name=resource_name, region_name=region_name, config=config)
        self.bucket = bucket
        self.tmp_bucket = tmp_bucket
        self.region_name = region_name
        self.size_limit = size_limit

        self.s3_client = boto3.client('s3', region_name=region_name, config=config)
        self.ecs = boto3.client('ecs', region_name=region_name, config=config)
        self.lambda_client = boto3.client('lambda')

    def save_new_route(self, bucket: str, key: str, name: str = None) -> None:
        resp = self.ecs.run_task(
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': ['subnet-0567cac0229946232'],
                    'securityGroups': ['sg-fe12c9b7'],
                    'assignPublicIp': 'ENABLED' # TODO: check if this is needed
                },
            },
            launchType='FARGATE',
            cluster='arn:aws:ecs:ap-southeast-2:950765595897:cluster/unzipper-cluster',
            taskDefinition='arn:aws:ecs:ap-southeast-2:950765595897:task-definition/unzipper-fargate:8',
            overrides={
                'containerOverrides': [
                    {
                        'name': 'unzipper', 
                        'command':  ['python', 'farg.py', bucket, key, self.region_name, name]
                    }
                ]
            }
        )

        if len(resp[self.ECS_TASKS_KEY]) < 1:
            raise ValueError(f'Unable to run any tasks, ecs returned the following response:', resp)

        print('unzipping execution begun:', resp)

        return str(resp)

    def begin_prediction(self, user_id: str, route_id: str) -> None:
        # self.mlapi.add_message_to_queue(user_id, route_id)
        pass

    def save_route(
        self, 
        route_spec: RouteSpec, 
        user_id: str, 
    ) -> Route:
        route_id = str(uuid.uuid1())

        print(f'uploading route {route_spec} as {route_id}')

        initial_entries = {}
        timestamp = 0

        for reading_spec in route_spec.reading_specs:
            print(f'starting upload for reading {reading_spec}')

            entries = reading_spec.load_readings()

            if len(entries) > 0:
                finalized_entries = self.__save_entries(route_id, reading_spec.reading_type, entries)
                first_entry: Reading = finalized_entries[0]
                initial_entries[reading_spec.reading_type] = first_entry

                if timestamp == 0:
                    timestamp = first_entry.date

                print('Finished saving all readings to FDS database')
            else:
                print(f'No entries found for reading specification {reading_spec}')

        route = Route(
            user_id=user_id,
            id=route_id,
            timestamp=timestamp,
            name=route_spec.name if route_spec.name else None,
            sample_data=initial_entries
        )

        self.put_route(route)
        print(f'Finished uploading route {route_id} for user {user_id}')

        return route

    def __same_image(self, r1: Dict[str, Any], r2: Dict[str, Any]) -> bool:
        r1 = r1[Constants.READING]
        r2 = r2[Constants.READING]

        if Constants.FILENAME in r1 and\
            Constants.FILENAME in r2 and\
            r2[Constants.FILENAME] == r1[Constants.FILENAME]:
            return True
        if Constants.URI in r1 and\
            Constants.URI in r2 and\
            r1[Constants.URI][Constants.BUCKET] == r2[Constants.URI][Constants.BUCKET] and\
            r1[Constants.URI][Constants.KEY] == r2[Constants.URI][Constants.KEY]:
            return True
        
        return False

    def save_predictions(
        self, 
        readings: List[Dict[str, Any]], 
        route_id: int, 
        save_imgs: bool = True
    ) -> None:
        existing_readings = self.all_route_readings(route_id, size_limit=99999999999)
        
        to_delete = set()
        for r in readings:
            saved = False
            for er in existing_readings:
                if self.__same_image(r, er):
                    if not save_imgs:
                        r[Constants.READING][Constants.URI] = er[Constants.READING][Constants.URI]
                    saved=True

                    if (er[Constants.TYPE] == Constants.PREDICTION and er[Constants.ANNOTATOR_ID] == r[Constants.ANNOTATOR_ID]):
                        to_delete.add(er[Constants.READING_ID]) 
            
            if not saved and not save_imgs:
                raise ValueError(f'could not find an existing reading with the same image as {r} and saving images has been disallowed')
        
        self.delete_reading_items(route_id, list(to_delete))

        saved_entries = self.__save_entries(route_id, Constants.PREDICTION, readings, save_imgs)
        return saved_entries

    def set_as_predicting(self, route_id: str, user_id: str) -> None:
        self.set_route_status(route_id, user_id, RouteStatus.PREDICTING)

    def all_route_readings_async(self, route_id: str, access_token: str) -> str:
        bucket_key = str(uuid.uuid1()) + '.json'
        pl = {
            'Type': 'GetReadings',
            'BucketKey': bucket_key,
            'RouteID': route_id,
            'AccessToken': access_token,
        }

        self.lambda_client.invoke(
            FunctionName=LAMBDA_ENDPOINT,
            InvocationType='Event',
            Payload=json.dumps(pl)
        )

        return {Constants.BUCKET: self.tmp_bucket, Constants.KEY: bucket_key}

    def all_route_readings(
        self, 
        route_id: str, 
        key: str = None, 
        size_limit = None,
        predictions_only = False,
        annotator_preference = None
    ) -> List[Dict[str, Any]]:
        readings = super().all_route_readings(route_id)

        if predictions_only:
            readings = [r for r in readings if r['Type'] == Constants.PREDICTION]

        if annotator_preference:
            readings = self.__preferred_readings(annotator_preference, readings)


        self.__inject_presigned_urls(readings)
        
        if size_limit is None:
            size_limit = self.size_limit

        # Lambda cannot send responses that are larger than
        # 6 mb in size. The JSON for the readings will often
        # be larger than 6mb.
        reading_json = json.dumps(readings)
        resp_size = sys.getsizeof(reading_json)
        print('response size:', resp_size)
        if resp_size > size_limit:
            s3_key = str(uuid.uuid1()) + '.json' if key is None else key
            self.s3_client.put_object(
                Body=str(json.dumps(readings)),
                Bucket = self.tmp_bucket,
                Key=s3_key
            )

            return { Constants.BUCKET: self.tmp_bucket, Constants.KEY: s3_key }

        return readings

    def prediction_readings(
        self, 
        route_id: str, 
        annotator_preference: List[str] = [],
        key: str = None, 
        size_limit: int = None,
    )-> List[Dict[str, Any]]:

        return self.all_route_readings(
            route_id, 
            key, 
            size_limit,
            predictions_only=True,
            annotator_preference=annotator_preference,
        )

    def get_route(self, route_id: str, user_id: str) -> Dict[str, Any]:
        r = super().get_route(route_id, user_id)
        if not r:
            return r

        self.__inject_samples_with_presigned_urls(r)

        return r

    def filtered_paginated_readings(
        self, 
        route_id: str, 
        annotator_preference,
        last_key: str = None,
    ) -> Tuple[List[Dict[str, Any]], str]:
        return self.paginated_route_readings(
            route_id,
            last_key,
            predictions_only=True,
            annotator_preference=annotator_preference
        )

    def paginated_route_readings(
        self, 
        route_id: str, 
        last_key: str = None,
        predictions_only = False,
        annotator_preference = None
    ) -> Tuple[List[Dict[str, Any]], str]:
        readings, next_key = super().paginated_route_readings(route_id, last_key)
    
        if predictions_only:
            readings = [r for r in readings if self.__is_prediction_reading(r)]

        if annotator_preference:
            paginated_uris = [self.__uri_str(r) for r in readings if\
                self.__is_prediction_reading(r)]

            paginated_ids = [r[Constants.READING_ID] for r in readings]
            all_readings = self.all_route_readings(
                route_id, 
                predictions_only=predictions_only, 
                size_limit=9999999
            )
            relevent_readings = [r for r in all_readings if\
                self.__is_prediction_reading(r) and\
                self.__uri_str(r) in paginated_uris and not\
                r[Constants.READING_ID] in paginated_ids]
            preferred = self.__preferred_readings(annotator_preference, readings + relevent_readings)
            readings = [r for r in readings if r in preferred]

        self.__inject_presigned_urls(readings)
        return readings, next_key

    def delete_route(self, route_id: str, user_sub: str) -> Any:
        deletedImgCount = 0

        readings = self.all_route_readings(route_id)

        for r in readings:
            if r[Constants.TYPE] == Constants.PREDICTION or \
                r[Constants.TYPE] == Constants.IMAGE:
                reading = r[Constants.READING]
                if Constants.URI in reading:
                    uri = reading[Constants.URI]
                    resp = self.s3_client.delete_object(
                        Bucket=uri[Constants.BUCKET],
                        Key=uri[Constants.KEY]
                    )

        deletedReadingCount = self.delete_reading_items(
            route_id, 
            [r[Constants.READING_ID] for r in readings]
        )

        table = self.db.Table('Routes')
        
        table.delete_item(
            Key={
                Constants.ROUTE_ID: route_id,
                Constants.USER_ID: user_sub
            }
        )

        return (deletedReadingCount, deletedImgCount)

    def __preferred_readings(self, preference: List[str], readings: Dict[str, Any]) -> None:
        reading_groups = defaultdict(lambda: [])
        final_readings = []

        for r in readings:
            if self.__is_prediction_reading(r):
                reading_groups[self.__uri_str(r)].append(r)
            else:
                final_readings.append(r)

        for g in reading_groups.values():
            final_readings.append(sorted(
                g,
                key=lambda r: self.__annotator_precedence(preference, r[Constants.ANNOTATOR_ID])
            )[0])
            
        return final_readings

    def __uri_str(self, reading: Dict[str, Any]) -> str:
        uri = reading[Constants.READING][Constants.URI]
        return uri[Constants.BUCKET] + '/' + uri[Constants.KEY]

    def __is_prediction_reading(self, r: Dict[str, Any]) -> bool:
        return r[Constants.TYPE] == Constants.PREDICTION

    def __annotator_precedence(self, annotators: List[str], annotator: str) -> int:
        if annotator == FAUX_ANNOTATOR_ID:
            return len(annotators) + 1

        if not annotator in annotators:
            return len(annotators)
        
        return annotators.index(annotator)

    def __inject_samples_with_presigned_urls(self, route: Dict[str, Any]) -> None:
        if Constants.SAMPLE_DATA in route:
            for _, sample in route[Constants.SAMPLE_DATA].items():
                self.__inject_presigned_url(sample)

    def __inject_presigned_urls(self, readings: List[Dict[str, Any]]) -> None:
        for r in readings:
            self.__inject_presigned_url(r)
    
    def __inject_presigned_url(self, r: Dict[str, Any]) -> None:    
        if Constants.URI in r[Constants.READING]:
            uri = r[Constants.READING][Constants.URI]

            r[Constants.READING][Constants.PRESIGNED_URL] = self.__presigned_url(
                uri[Constants.BUCKET],
                uri[Constants.KEY],
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

    def __save_entry_data(self, entry: Reading, save_img=True) -> AbstractReading:
        if entry.readingType in Constants.IMAGE_TYPES and save_img:
            self.__save_img_data(entry)

        return entry

    def __save_img_data(self, entry: ImageReading):
        if not entry.has_uri():
            uri: S3Uri = self.__upload_entry_file(entry)
            entry.set_uri(uri)

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

    def __save_entries(self, route_id, entry_type, entries, save_img=True) -> List[AbstractReading]:
        finalized: List[AbstractReading] = []
        n_entries = len(entries)
        for i, e in enumerate(entries):
            if i % 10 == 0:
                print(f'uploading entry {i} of {n_entries}')

            e = self.__json_to_entry(e, entry_type, str(uuid.uuid1()), route_id)
            e = self.__save_entry_data(e, save_img)
            finalized.append(e)

        self.put_readings(finalized)

        return finalized

    def __json_to_entry(self, e: Dict[str, Any], entry_type: str, reading_id: str, route_id: str) -> Reading:
        e[Constants.READING_ID] = reading_id
        e[Constants.ROUTE_ID] = route_id
        return json_to_reading(entry_type, e)

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- ROUTE --------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def routes_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        routes = super().routes_for_user(user_id)
        for r in routes:
            self.__inject_samples_with_presigned_urls(r)
        
        return routes

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- USER ---------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def save_user(self, uid: str, data_access_groups: List[Dict[str, str]] = []) -> bool:
        all_users = self.all_users()

        for u in all_users:
            if u[Constants.USER_ID] == uid:
                return False
        
        return self.put_user(uid, data_access_groups)

        