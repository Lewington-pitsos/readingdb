import boto3
import zipfile

from readingdb.readingspec import ReadingSpec
from readingdb.routespec import RouteSpec
from readingdb.constants import *
from readingdb.s3uri import S3Uri

class Unzipper():
    OBJ_BODY_KEY = "Body"

    def __init__(self, config=None) -> None:
        self.s3_resource = boto3.resource('s3')

    def process(bucket: str, key: str) -> None:
        zip_obj = self.s3_resource.Object(bucket_name=bucket, key=key)
        buffer = BytesIO(zip_obj.get()[self.OBJ_BODY_KEY].read())
        
        readingTypes = set()

        z = zipfile.ZipFile(buffer)
        for filename in z.namelist():
            file_info = z.getinfo(filename)
            s3_filename = f'{key.split(".")[0]}/{filename}'
            print("creating new file:", s3_filename)
            self.s3_resource.meta.client.upload_fileobj(
                z.open(filename),
                Bucket=bucket,
                Key=s3_filename
            )

            readingTypes.add(self.__reading_spec(bucket, s3_filename))

        # sends a request to the RaedingDB lambda to upload that routespec

        routeSpec = RouteSpec(list(readingTypes))

    def __reading_spec(self, bucket: str, filename: str) -> ReadingSpec:
        extension = filename.split(".")[-1]

        if extension == ".jpg":
            return ReadingSpec(
                ReadingTypes.IMAGE, 
                ReadingSpec.S3_FILES_FORMAT, 
                S3Uri(bucket, filename)
            )
        elif extension == ".txt":
            return ReadingSpec(
                ReadingTypes.POSITIONAL, 
                ReadingSpec.S3_FILES_FORMAT, 
                S3Uri(bucket, filename)
            )
        else:
            raise ValueError("unrecognized reading file type: ", filename)
        
   


    class API(DB, ReadingDB):
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