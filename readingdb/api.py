import boto3
import copy

from readingdb.db import DB
from readingdb.normalize import *
from readingdb.constants import *
class API(DB):
    def __init__(self, url, resource_name='dynamodb', bucket="mobileappsessions172800-main"):
        super().__init__(url=url, resource_name=resource_name)
        self.bucket = bucket

        self.s3_client = boto3.client('s3')

        self.aws_loc = url.split("/")[-1].replace("dynamodb.", "")

    def upload_file(self, route_id, file_name, bucket):
        object_name = route_id + file_name        
        response = self.s3_client.upload_file(file_name, bucket, object_name)

        return response, object_name

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

    def s3_url(self, object_name):
        return f"https://{self.bucket}.s3.{self.aws_loc}/{object_name}" 

    def get_filename(self, entry_type, entry):
        if entry_type == ReadingTypes.IMAGE:
            if ImageReading.FILENAME not in entry:
                raise ValueError(f"Expected reading entry to have key {ImageReading.FILENAME}, no such keyw as found: {entry}")

            return entry[ImageReading.FILENAME]

        if entry_type == ReadingTypes.PREDICTION:
            if PredictionReading.BASIS not in entry or PredictionBasis.FILENAME not in entry[PredictionReading.BASIS]:
                raise ValueError(f"Expected reading entry to have key {ImageReading.FILENAME}, no such keyw as found: {entry}")

            return entry[PredictionReading.BASIS][PredictionBasis.FILENAME]


    def save_img_entry(self, entry_type, route_id, reading_id, entry):
        filename = self.get_filename(entry_type, entry)
        _, object_name = self.upload_file(route_id, filename, self.bucket)

        clone = copy.deepcopy(entry)
        clone[PredictionReading.BASIS][PredictionBasis.FILENAME] = self.s3_url(object_name)
        self.save_primitive_entry(entry_type, route_id, reading_id, clone)

        return clone


