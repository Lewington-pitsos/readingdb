import boto3
import zipfile
from io import BytesIO

from readingdb.readingspec import ReadingSpec
from readingdb.routespec import RouteSpec
from readingdb.constants import *
from readingdb.s3uri import S3Uri
from readingdb.format import *
from readingdb.api import API

class Unzipper():
    IMG_EXT = "jpg"
    TXT_EXT = "txt"

    OBJ_BODY_KEY = "Body"

    def __init__(self, url, *args, **kwargs) -> None:
        self.s3_resource = boto3.resource('s3')
        self.api: API = API(url, *args, **kwargs)

    def process(self, bucket: str, key: str) -> None:
        reading_types = {}
        img_readings = []
 
        zip_obj = self.s3_resource.Object(bucket_name=bucket, key=key)
        print(zip_obj.metadata)
        buffer = BytesIO(zip_obj.get()[self.OBJ_BODY_KEY].read())
        z = zipfile.ZipFile(buffer)
        
        for filename in z.namelist():
            print(filename)
            s3_filename = f'{key.split(".")[0]}/{filename}'
            print("creating new file:", s3_filename)

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
                
                reading_types[self.TXT_EXT] = ReadingSpec(
                    ReadingTypes.POSITIONAL, 
                    ReadingSpec.S3_FILES_FORMAT, 
                    S3Uri(bucket, s3_filename)
                )
            else:
                raise ValueError("unrecognized reading file type: ", s3_filename)

        # sends a request to the RaedingDB lambda to upload that routespec

        user_id = zip_obj.metadata[RouteKeys.USER_ID.lower()]
        if self.IMG_EXT in reading_types:
            reading_types[self.IMG_EXT].data = img_readings

        routeSpec = RouteSpec(list(reading_types.values()))

        self.api.save_route(routeSpec, user_id)

    def __file_type(filename):
        extension = filename.split(".")[-1]



    def __reading_spec(self, bucket: str, filename: str) -> ReadingSpec:
        extension = filename.split(".")[-1]

        if extension == "jpg":
            return ReadingSpec(
                ReadingTypes.IMAGE, 
                ReadingSpec.S3_FILES_FORMAT, 
                S3Uri(bucket, filename)
            )
        elif extension == self.TXT_EXT:
            return ReadingSpec(
                ReadingTypes.POSITIONAL, 
                ReadingSpec.S3_FILES_FORMAT, 
                S3Uri(bucket, filename)
            )
        else:
            raise ValueError("unrecognized reading file type: ", filename)
        