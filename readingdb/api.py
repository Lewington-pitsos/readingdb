import boto3
import copy

from boto3.dynamodb.conditions import Key

from readingdb.db import DB
from readingdb.normalize import *
from readingdb.constants import *

class API(DB):
    def __init__(
        self, 
        url, 
        auth,
        resource_name='dynamodb', 
        bucket="mobileappsessions172800-main",
        config=None
    ):
        super().__init__(url=url, auth=auth, resource_name=resource_name, config=config)
        self.bucket = bucket

        self.s3_client = boto3.client('s3', config=config)

    def upload_file(self, route_id, file_name, bucket):
        object_name = route_id + file_name        
        response = self.s3_client.upload_file(file_name, bucket, object_name)

        return response, object_name

    # def routes_for_user(user_id):
        

    def save_entry(self, entry_type, route_id, reading_id, entry):
        if entry_type in ReadingTypes.IMAGE_TYPES:
            return self.save_img_entry(entry_type, route_id, reading_id, entry)

        return self.save_primitive_entry(entry_type, route_id, reading_id, entry)

    def save_primitive_entry(self, entry_type, route_id, reading_id, entry):
        ts = entry[EntryKeys.TIMESTAMP]

        if isinstance(ts, float):
            ts = int(ts)

        self.put_reading(
            route_id,
            reading_id,
            entry_type,
            entry,
            ts
        )

        return entry

    def save_img_entry(self, entry_type, route_id, reading_id, entry):
        if ImageReadingKeys.FILENAME not in entry:
                raise ValueError(f"Expected reading entry to have key {ImageReadingKeys.FILENAME}, no such keyw as found: {entry}")

        _, object_name = self.upload_file(route_id, entry[ImageReadingKeys.FILENAME], self.bucket)

        clone = copy.deepcopy(entry)
        clone[ImageReadingKeys.FILENAME] = {
            S3Path.BUCKET: self.bucket,
            S3Path.KEY: object_name
        }
        self.save_primitive_entry(entry_type, route_id, reading_id, clone)

        return clone


