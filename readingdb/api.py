from collections import defaultdict
import json
import sys
from readingdb.routestatus import RouteStatus
from typing import Any, Dict, List, Tuple
from readingdb.s3uri import S3Uri
from readingdb.route import Route
from readingdb.reading import PredictionReading, Reading, json_to_reading
from readingdb.routespec import RouteSpec
import boto3
import uuid

from readingdb.db import DB
from readingdb.endpoints import LAMBDA_ENDPOINT
from readingdb.constants import *

class API(DB):
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

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- READINGS -----------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

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
        route_id: str, 
        user_id: str,
        save_imgs: bool = True,
        layer_id: str = None
    ) -> None:
        existing_readings = self.all_route_readings(route_id, user_id, size_limit=99999999999)
        
        to_delete = {}
        for r in readings:
            saved = False
            for er in existing_readings:
                if self.__same_image(r, er):
                    if not save_imgs:
                        r[Constants.READING][Constants.URI] = er[Constants.READING][Constants.URI]
                    saved=True

                    if (er[Constants.TYPE] == Constants.PREDICTION and er[Constants.ANNOTATOR_ID] == r[Constants.ANNOTATOR_ID]):
                        to_delete[er[Constants.READING_ID]] = er 
            
            if not saved and not save_imgs:
                raise ValueError(f'could not find an existing reading with the same image as {r} and saving images has been disallowed')
        
        self.delete_reading_items(to_delete.values())
        saved_entries = self.__save_entries(route_id, Constants.PREDICTION, readings, save_imgs)

        if layer_id is not None:
            reading_data = []
            for e in saved_entries:
                reading_data.append(e.query_data())     
            self.add_readings_to_layer(layer_id, reading_data)

        return saved_entries


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
        user_id: str,
        key: str = None, 
        size_limit = None,
        predictions_only = False,
        annotator_preference = None
    ) -> List[Dict[str, Any]]:
        readings = super().all_route_readings(route_id, user_id)

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
        user_id: str,
        annotator_preference: List[str] = [],
        key: str = None, 
        size_limit: int = None,
    )-> List[Dict[str, Any]]:

        return self.all_route_readings(
            route_id, 
            user_id,
            key, 
            size_limit,
            predictions_only=True,
            annotator_preference=annotator_preference,
        )

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

    def __save_entry_data(self, entry: Reading, save_img=True) -> PredictionReading:
        if entry.reading_type in Constants.IMAGE_TYPES and save_img:
            self.__save_img_data(entry)

        return entry

    def __save_img_data(self, entry: PredictionReading):
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

    def __save_entries(self, route_id, entry_type, entries, save_img=True) -> List[PredictionReading]:
        finalized: List[PredictionReading] = []
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

    def save_route(
        self, 
        route_spec: RouteSpec, 
        user_id: str, 
        layer_id: str
    ) -> Route:
        route_id = str(uuid.uuid1())

        print(f'uploading route {route_spec} as {route_id}')

        initial_entries = {}
        timestamp = 0
        geohashes = set()

        all_entries = []
        for reading_spec in route_spec.reading_specs:
            print(f'starting upload for reading {reading_spec}')

            entries = reading_spec.load_readings()

            if len(entries) > 0:
                finalized_readings = self.__save_entries(route_id, reading_spec.reading_type, entries)

                for e in finalized_readings:
                    geohashes.add(e.geohash())

                first_entry: Reading = finalized_readings[0]
                initial_entries[reading_spec.reading_type] = first_entry

                if timestamp == 0:
                    timestamp = first_entry.date

                all_entries.extend([r.query_data() for r in finalized_readings])

                print('Finished saving all readings to FDS database')
            else:
                print(f'No entries found for reading specification {reading_spec}')

        self.add_readings_to_layer(layer_id, all_entries)

        route = Route(
            user_id=user_id,
            id=route_id,
            timestamp=timestamp,
            name=route_spec.name if route_spec.name else None,
            geohashes=geohashes,
            sample_data=initial_entries
        )

        self.put_route(route)
        print(f'Finished uploading route {route_id} for user {user_id}')

        return route

    def routes_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        routes = super().routes_for_user(user_id)
        for r in routes:
            self.__inject_samples_with_presigned_urls(r)
        
        return routes

    def set_as_predicting(self, route_id: str, user_id: str) -> None:
        self.set_route_status(route_id, user_id, RouteStatus.PREDICTING)

    def delete_route(self, route_id: str, user_sub: str) -> Any:
        deletedImgCount = 0

        readings = self.all_route_readings(route_id, user_sub)

        for r in readings:
            if r[Constants.TYPE] == Constants.PREDICTION:
                reading = r[Constants.READING]
                if Constants.URI in reading:
                    uri = reading[Constants.URI]
                    self.s3_client.delete_object(
                        Bucket=uri[Constants.BUCKET],
                        Key=uri[Constants.KEY]
                    )

        deletedReadingCount = self.delete_reading_items(readings)

        self.remove_route(route_id, user_sub)

        return (deletedReadingCount, deletedImgCount)

    def get_route(self, route_id: str, user_id: str) -> Dict[str, Any]:
        r = super().get_route(route_id, user_id)
        if not r:
            return r

        self.__inject_samples_with_presigned_urls(r)

        return r

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- USER ---------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def save_user(self, uid: str, data_access_groups: List[Dict[str, str]] = []) -> None:
        all_users = self.all_users()

        already_exists = False

        for u in all_users:
            if u[Constants.USER_ID] == uid:
                already_exists = True
                break
        
        if not already_exists:
            self.put_user(uid)

        for ag in data_access_groups:
            group_id = ag[Constants.GROUP_ID]
            self.user_add_group(uid, group_id)
            if Constants.GROUP_NAME in ag:
                self.put_group(group_id, ag[Constants.GROUP_NAME])

        