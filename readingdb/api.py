import boto3
import copy

from readingdb.db import DB
from readingdb.normalize import *
from readingdb.constants import *
class API(DB):
    def __init__(self, url, resource_name='dynamodb', bucket="mobileappsessions172800-main"):
        super().__init__(url=url, resource_name=resource_name)
        self.bucket = bucket
        if self.bucket[-1] != "/":
            self.bucket += "/"

        self.s3_client = boto3.client('s3')

    def upload_file(self, route_id, file_name, bucket):
        object_name = route_id + file_name        
        response = self.s3_client.upload_file(file_name, bucket, object_name)

        return response, object_name

    def save_entry(self, route_id, user_id, reading_id, entry):

        ts = entry[EntryKeys.TIMESTAMP]

        if isinstance(ts, float):
            ts = int(ts)
        self.put_reading(
            route_id,
            reading_id,
            ReadingTypes.PREDICTION,
            entry_to_prediction(entry),
            ts
        )

    def s3_url(self, object_name):
        return "https://" + self.bucket + object_name

    def save_img_entry(self, route_id, user_id, reading_id, entry):
        if ImageReading.FILENAME not in entry:
            raise ValueError(f"Expected reading entry to have key {ImageReading.FILENAME}, no such keyw as found: {entry}")
        
        _, object_name = self.upload_file(route_id, entry[ImageReading.FILENAME], self.bucket)

        clone = copy.deepcopy(entry)
        clone[ImageReading.FILENAME] = self.s3_url(object_name)
        self.save_entry(route_id, user_id, reading_id, clone)