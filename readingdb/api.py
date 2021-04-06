import boto3
import copy
import json
import time
import random
import string
import tqdm

from boto3.dynamodb.conditions import Key

from readingdb.db import DB
from readingdb.normalize import *
from readingdb.constants import *

def load_json_entries(path_key, reading):
    with open(reading[path_key], "r") as f:
        entries = json.load(f)
    
    return entries

class API(DB):
    ROUTE_NAME_KEY = "route"
    ROUTE_READINGS_KEY = "readings"
    READING_TYPE_KEY = "type"
    READING_FORMAT_KEY = "format"
    READING_PATH_KEY = "path"

    JSON_ENTRIES_FORMAT = "json_entries"

    RECOGNIZED_READING_TYPES = {
        ReadingTypes.IMAGE:{
            JSON_ENTRIES_FORMAT: load_json_entries
        },
        ReadingTypes.POSITIONAL:{
            JSON_ENTRIES_FORMAT: load_json_entries
        },
        ReadingTypes.PREDICTION:{
            JSON_ENTRIES_FORMAT: load_json_entries
        }
    }
    
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

    def __upload_file(self, route_id, file_name, bucket):
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

        _, object_name = self.__upload_file(route_id, entry[ImageReadingKeys.FILENAME], self.bucket)

        clone = copy.deepcopy(entry)
        clone[ImageReadingKeys.FILENAME] = {
            S3Path.BUCKET: self.bucket,
            S3Path.KEY: object_name
        }
        self.save_primitive_entry(entry_type, route_id, reading_id, clone)

        return clone

    def upload(self, route):
        route_key = self.generate_route_id()
        route_id = str(time.time()) + "-" + route_key

        print(f"uploading route {route} as {route_id}")

        initial_entries = {}

        for reading in route[self.ROUTE_READINGS_KEY]:
            print(f"starting upload for reading {reading}")

            entries = self.load_reading(reading)    

            if len(entries) > 0:
                saved_entries = self.save_entries(route_id, reading[self.READING_TYPE_KEY], entries)
                initial_entries[reading[self.READING_TYPE_KEY]] = saved_entries[0]
                print("Finished saving all readings to FDS database")
            else:
                print("No entries found for reading specification")

        route_name = route[self.ROUTE_NAME_KEY] if self.ROUTE_NAME_KEY in route else route_key

        self.put_route(self.usr_sub, route_id, route_name, sample_data=initial_entries)
        print(f"Finished uploading route {route_id} for user {self.uname}")

    def load_reading(self, reading):
        reading_type = reading[self.READING_TYPE_KEY] 

        if reading_type not in self.RECOGNIZED_READING_TYPES:
            raise ValueError(f"Unrecognize reading type {reading_type} in reading specification {reading}")

        format_type = reading[self.READING_FORMAT_KEY] 

        if format_type not in self.RECOGNIZED_READING_TYPES[reading_type]:
            raise ValueError(f"Unrecognize format {format_type} for reading of type {reading_type} in reading specification {reading[self.READING_TYPE_KEY]} in reading {reading}")

        return self.RECOGNIZED_READING_TYPES[reading_type][format_type](self.READING_PATH_KEY, reading)

    def generate_route_id(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))

    def save_entries(self, route_id, entry_type, entries):
        saved_entries = []        

        print("uploading entries")
        for i, e in enumerate(tqdm(entries)):
            e = normalize(entry_type, e) 
            saved_entry = self.save_entry(
                entry_type,
                route_id,
                i+1,
                e 
            )

            saved_entries.append(saved_entry)

        return saved_entries