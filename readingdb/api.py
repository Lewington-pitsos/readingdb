import json
import sys
from readingdb import s3uri
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

    def save_route(self, route_spec: RouteSpec, user_id: str) -> Route:
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
        r1 = r1[ReadingKeys.READING]
        r2 = r2[ReadingKeys.READING]

        if ImageReadingKeys.FILENAME in r1 and\
            ImageReadingKeys.FILENAME in r2 and\
            r2[ImageReadingKeys.FILENAME] == r1[ImageReadingKeys.FILENAME]:
            return True
        
        if ImageReadingKeys.URI in r1 and\
            ImageReadingKeys.URI in r2 and \
            r1[ImageReadingKeys.URI][S3Path.BUCKET] == r2[ImageReadingKeys.URI][S3Path.BUCKET] and\
            r1[ImageReadingKeys.URI][S3Path.KEY] == r2[ImageReadingKeys.URI][S3Path.KEY]:
            return True
        
        return False

    def save_predictions(
        self, 
        readings: List[Dict[str, Any]], 
        route_id: int, 
        user_id: str, 
        save_imgs: bool = True
    ) -> None:
        if not save_imgs:
            existing_readings = self.all_route_readings(route_id, size_limit=99999999999)
            for r in readings:
                for er in existing_readings:
                    if self.__same_image(r, er):
                        r[ReadingKeys.READING][ImageReadingKeys.URI] = er[ReadingKeys.READING][ImageReadingKeys.URI]
                        break
                else:
                    raise ValueError(f'could not find an existing reading with the same image as {r} and saving images has been disallowed')
        
        self.__save_entries(route_id, ReadingTypes.PREDICTION, readings, save_imgs)
        self.set_route_status(route_id, user_id, RouteStatus.COMPLETE)

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

        return {S3Path.BUCKET: self.tmp_bucket, S3Path.KEY: bucket_key}

    def all_route_readings(self, route_id: str, key: str = None, size_limit = None) -> List[Dict[str, Any]]:
        readings = super().all_route_readings(route_id)
        self.__inject_presigned_urls(readings)
        
        if size_limit is None:
            size_limit = self.size_limit

        # Lambda cannot send responses that are larger than
        # 6 mb in size. The JSON for the readins will often
        # be larger than 6mb.
        if sys.getsizeof(readings) > size_limit:
            s3_key = str(uuid.uuid1()) + '.json' if key is None else key
            self.s3_client.put_object(
                Body=str(json.dumps(readings)),
                Bucket = self.tmp_bucket,
                Key=s3_key
            )

            return { S3Path.BUCKET: self.tmp_bucket, S3Path.KEY: s3_key }

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

    def paginated_route_readings(self, route_id: str, last_key: str = None) -> Tuple[List[Dict[str, Any]], str]:
        readings, next_key = super().paginated_route_readings(route_id, last_key)

        self.__inject_presigned_urls(readings)
        return readings, next_key

    def delete_route(self, route_id: str, user_sub: str) -> Any:
        deletedImgCount = 0

        readings = self.all_route_readings(route_id)

        for r in readings:
            if r[ReadingKeys.TYPE] == ReadingTypes.PREDICTION or \
                r[ReadingKeys.TYPE] == ReadingTypes.IMAGE:
                reading = r[ReadingKeys.READING]
                if ImageReadingKeys.URI in reading:
                    uri = reading[ImageReadingKeys.URI]
                    resp = self.s3_client.delete_object(
                        Bucket=uri[S3Path.BUCKET],
                        Key=uri[S3Path.KEY]
                    )


        deletedReadingCount = self.delete_reading_items(
            route_id, 
            [r[ReadingKeys.READING_ID] for r in readings]
        )

        table = self.db.Table('Routes')
        
        table.delete_item(
            Key={
                ReadingRouteKeys.ROUTE_ID: route_id,
                RouteKeys.USER_ID: user_sub
            }
        )

        return (deletedReadingCount, deletedImgCount)
        
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

    def __save_entry_data(self, entry: Reading, save_img=True) -> AbstractReading:
        if entry.readingType in ReadingTypes.IMAGE_TYPES and save_img:
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
        e[ReadingKeys.READING_ID] = reading_id
        e[ReadingRouteKeys.ROUTE_ID] = route_id
        return json_to_reading(entry_type, e)