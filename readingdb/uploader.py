import boto3
import json
import random
import string

from datetime import datetime
from readingdb.api import API
class Uploader():
    @staticmethod
    def load_json_entries(path_key, reading):
        with open(reading[path_key], "r") as f:
            entries = json.load(f)
        
        return entries

    AUTH_RESULT_KEY = "AuthenticationResult"
    ACCESS_TOKEN_KEY = "AccessToken"
    USER_ATTR_KEY = "UserAttributes"
    ATTR_NAME_KEY = "Name"
    ATTR_VALUE_KEY = "Value"
    USERNAME_KEY = "Username"

    USER_SUB = 'sub'
    
    ROUTE_NAME_KEY = "route"
    ROUTE_READINGS_KEY = "readings"
    READING_TYPE_KEY = "type"
    READING_FORMAT_KEY = "format"
    READING_PATH_KEY = "path"

    GPS_TYPE = "gps"
    CAMERA_TYPE = "camera"
    JSON_ENTRIES_FORMAT = "json_entries"

    RECOGNIZED_READING_TYPES = {
        CAMERA_TYPE:{
            JSON_ENTRIES_FORMAT: load_json_entries
        },
        GPS_TYPE: {
            JSON_ENTRIES_FORMAT: load_json_entries
        }
    }

    def __init__(self, auth, region_name="ap-southeast-2", ddburl="https://dynamodb.ap-southeast-2.amazonaws.com"):
        cclient = boto3.client('cognito-idp', region_name=region_name)

        auth_resp = cclient.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': auth.username,
                'PASSWORD': auth.password},
            ClientId=auth.clientid)

        if not self.ACCESS_TOKEN_KEY in auth_resp[self.AUTH_RESULT_KEY]:
            raise ValueError(f"Unexpected cognito authentication response: {auth_resp}")

        self.access_token = auth_resp[self.AUTH_RESULT_KEY][self.ACCESS_TOKEN_KEY]
        user_resp = cclient.get_user(AccessToken=auth_resp[self.AUTH_RESULT_KEY][self.ACCESS_TOKEN_KEY])

        self.uname = user_resp[self.USERNAME_KEY]

        for attr in user_resp[self.USER_ATTR_KEY]:
            if attr[self.ATTR_NAME_KEY] == self.USER_SUB:
                self.usr_sub = attr[self.ATTR_VALUE_KEY]
                break
        else:
            raise ValueError(f"Could not identify a user sub value in user response: {user_resp}")

        self.api = API(url=ddburl)

    def load_reading(self, reading):
        reading_type = reading[self.READING_TYPE_KEY] 

        if reading_type not in self.RECOGNIZED_READING_TYPES:
            raise ValueError(f"Unrecognize reading type {reading_type} in reading specification {reading}")

        format_type = reading[self.READING_FORMAT_KEY] 

        if format_type not in self.RECOGNIZED_READING_TYPES[reading_type]:
            raise ValueError(f"Unrecognize format {format_type} for reading of type {reading_type} in reading specification {reading[self.READING_TYPE_KEY]} in reading {reading}")

        return self.RECOGNIZED_READING_TYPES[reading_type][format_type](self.READING_PATH_KEY, reading)

    def generate_route_id(self):
        return str(datetime.utcnow()) + "_" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))

    def save_entries(self, route_id, entry_type, entries):
        for i, e in enumerate(entries):
            self.api.save_entry(
                route_id,
                self.usr_sub,
                i+1,
                e 
            )

    def upload(self, route):
        route_id = self.generate_route_id()
        print(f"uploading route {route} as {route_id}")

        initial_entries = {}

        for reading in route[self.ROUTE_READINGS_KEY]:
            print(f"starting upload for reading {reading}")

            entries = self.load_reading(reading)    

            if len(entries) > 0:
                initial_entries[reading[self.READING_TYPE_KEY]] = entries[0]
                self.save_entries(route_id, reading[self.READING_TYPE_KEY], entries)
                print("Finished saving all readings to FDS database")
            else:
                print("No entries found for reading specification")