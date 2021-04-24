from readingdb.mlapi import MLAPI
from readingdb.endpoints import SQS_URL
from readingdb.route import Route
import boto3
import zipfile
from io import BytesIO

from readingdb.readingspec import ReadingSpec
from readingdb.routespec import RouteSpec
from readingdb.constants import *
from readingdb.format import *
from readingdb.api import API

class Unzipper():
    IMG_EXT = "jpg"
    TXT_EXT = "txt"
    OBJ_BODY_KEY = "Body"

    def __init__(self, url:str, sqs_url: str=SQS_URL, *args, **kwargs) -> None:
        self.s3_resource = boto3.resource('s3')
        self.api: API = API(url, *args, **kwargs)
        self.mlapi = MLAPI(sqs_url)

    def process(self, bucket: str, key: str) -> Route:
        print("bucket", bucket)
        print("key", key)
        reading_types = {}
        img_readings = []
 
        zip_obj = self.s3_resource.Object(bucket_name=bucket, key=key)
        print("metadata", zip_obj.metadata)
        buffer = BytesIO(zip_obj.get()[self.OBJ_BODY_KEY].read())
        z = zipfile.ZipFile(buffer)
        
        for filename in z.namelist():
            print(filename)
            s3_filename = f'{key.split(".")[0]}/{filename}'
            print("extracting file:", s3_filename)

            self.s3_resource.meta.client.upload_fileobj(
                z.open(filename),
                Bucket=bucket,
                Key=s3_filename
            )

            extension = s3_filename.split(".")[-1]

            if extension == self.IMG_EXT:
                if self.IMG_EXT not in reading_types:
                    reading_types[self.IMG_EXT] = ReadingSpec(
                        ReadingTypes.IMAGE, 
                        ReadingSpec.S3_FILES_FORMAT, 
                        ""
                    )
                
                img_readings.append(entry_from_file(bucket, s3_filename))
            elif extension == self.TXT_EXT:
                if self.TXT_EXT in reading_types:
                    raise ValueError(f"found two .txt files when unzipping {key} of bucket {bucket}, this should never happen")

                with z.open(filename) as f:
                    lines = [b.decode('unicode_escape') for b in f.readlines()]

                points = txt_to_points(lines)

                reading_types[self.TXT_EXT] = ReadingSpec(
                    ReadingTypes.POSITIONAL, 
                    ReadingSpec.S3_FILES_FORMAT, 
                    points
                )
            else:
                raise ValueError("unrecognized reading file type: ", s3_filename)

        # sends a request to the RaedingDB lambda to upload that routespec

        user_id = zip_obj.metadata[RouteKeys.USER_ID.lower()]
        if self.IMG_EXT in reading_types:
            reading_types[self.IMG_EXT].data = img_readings

        routeSpec = RouteSpec(list(reading_types.values()))

        print("saving readings to route database")
        route = self.api.save_route(routeSpec, user_id)

        print("deleting zipped route: ", key)

        self.s3_resource.Object(bucket, key).delete()

        self.mlapi.add_message_to_queue(user_id, route.id)

        return route
