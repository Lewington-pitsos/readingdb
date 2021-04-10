import boto3
import zipfile
from io import BytesIO

from readingdb.readingspec import ReadingSpec
from readingdb.routespec import RouteSpec
from readingdb.constants import *
from readingdb.s3uri import S3Uri
from readingdb.api import API

class Unzipper():
    OBJ_BODY_KEY = "Body"

    def __init__(self, url) -> None:
        self.s3_resource = boto3.resource('s3')
        self.api: API = API(url)

    def process(self, bucket: str, key: str) -> None:
        zip_obj = self.s3_resource.Object(bucket_name=bucket, key=key)
        print(zip_obj.metadata)
        buffer = BytesIO(zip_obj.get()[self.OBJ_BODY_KEY].read())
        
        readingTypes: set = set()

        z = zipfile.ZipFile(buffer)
        for filename in z.namelist():
            print(filename)
            file_info = z.getinfo(filename)
            print(file_info)
            s3_filename = f'{key.split(".")[0]}/{filename}'
            print("creating new file:", s3_filename)
            self.s3_resource.meta.client.upload_fileobj(
                z.open(filename),
                Bucket=bucket,
                Key=s3_filename
            )

            readingTypes.add(self.__reading_spec(bucket, s3_filename))

        # sends a request to the RaedingDB lambda to upload that routespec

        user_id = zip_obj.metadata[RouteKeys.USER_ID]
        routeSpec = RouteSpec(list(readingTypes))

        self.api.save_route(routeSpec, user_id)

    def __reading_spec(self, bucket: str, filename: str) -> ReadingSpec:
        extension = filename.split(".")[-1]

        if extension == "jpg":
            return ReadingSpec(
                ReadingTypes.IMAGE, 
                ReadingSpec.S3_FILES_FORMAT, 
                S3Uri(bucket, filename)
            )
        elif extension == "txt":
            return ReadingSpec(
                ReadingTypes.POSITIONAL, 
                ReadingSpec.S3_FILES_FORMAT, 
                S3Uri(bucket, filename)
            )
        else:
            raise ValueError("unrecognized reading file type: ", filename)
        