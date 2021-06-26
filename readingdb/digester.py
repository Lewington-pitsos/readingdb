from readingdb.rutils import RUtils
from readingdb.geolocator import Geolocator
from typing import List
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

class Digester():
    IMG_EXT = 'jpg'
    TXT_EXT = 'txt'
    OBJ_BODY_KEY = 'Body'

    def __init__(self, url:str, sqs_url: str=SQS_URL, api=None, *args, **kwargs) -> None:
        self.s3_resource = boto3.resource('s3')
        if api is None:
            self.api: API = API(url, *args, **kwargs)
        else:
            self.api = api
        self.mlapi = MLAPI(sqs_url)

    def process(
        self, 
        bucket: str, 
        key: str, 
        name: str = None,
        snap_to_roads=False
    ) -> Route: 
        zip_obj = self.s3_resource.Object(bucket_name=bucket, key=key)
        print('metadata', zip_obj.metadata)
        user_id = zip_obj.metadata[RouteKeys.USER_ID.lower()]
        buffer = BytesIO(zip_obj.get()[self.OBJ_BODY_KEY].read())
        z = zipfile.ZipFile(buffer)

        def upload(filename, bucket, s3_filename):
            self.s3_resource.meta.client.upload_fileobj(
                z.open(filename),
                Bucket=bucket,
                Key=s3_filename
            )

        def read_gps_file(filename):
            with z.open(filename) as f:
                lines = [b.decode('unicode_escape') for b in f.readlines()]

            return lines

        route = self.__process_names(
            upload, 
            read_gps_file, 
            user_id, 
            key.split(".")[0], 
            bucket, 
            z.namelist(), 
            name,
            snap_to_roads=snap_to_roads
        )
        self.s3_resource.Object(bucket, key).delete()
        self.mlapi.add_message_to_queue(user_id, route.id)

        return route

    def process_upload(
        self, 
        user_id: str, 
        key: str, 
        bucket: str, 
        name: str = None,
        snap_to_roads=False,
    ):
        def upload(filename, bucket, s3_filename):
            pass

        s3_bucket = self.s3_resource.Bucket(bucket)
        bucket_objects = [o.key for o in s3_bucket.objects.filter(Prefix=key)]

        def read_gps_file(filename):
            obj = s3_bucket.Object(filename)
            body = obj.get()['Body'].read()

            return [l.decode("utf-8")  for l in body.split(b'\r')]

        return self.__process_names(
            upload, 
            read_gps_file, 
            user_id, 
            key, 
            bucket, 
            bucket_objects,
            name,
            snap_to_roads,
        )

    def process_local(
        self, 
        user_id: str, 
        key: str, 
        bucket: str, 
        filenames: List[str],
        name: str = None,
        snap_to_roads=False,
    ):
        def upload(filename, bucket, s3_filename):
            segs = s3_filename.split('/')

            self.s3_resource.meta.client.upload_file(
                filename,
                Bucket=bucket,
                Key= segs[0] + '/' + segs[-1]
            )

        def read_gps_file(filename):
            with open(filename) as f:
                lines = f.readlines()

            return lines

        return self.__process_names(
            upload, 
            read_gps_file, 
            user_id, 
            key, 
            bucket, 
            filenames, 
            name,
            snap_to_roads,
        )

    def __process_names(
        self, 
        upload, 
        read_gps_file, 
        user_id: str, 
        key: str, 
        bucket: str, 
        filenames: List[str], 
        name: str = None,
        snap_to_roads=False
    ):
        points, img_readings, filename_map = self.get_readings(
            filenames,
            key,
            bucket,
            read_gps_file,
        )

        g = Geolocator()
        if snap_to_roads:
            pred_readings = g.generate_predictions(points, img_readings)
        else:
            pred_readings = g.interpolated(points, img_readings)
        print('finished generating prediction readings')

        for r in pred_readings:
            uri = RUtils.get_uri(r)
            print('uploading', uri)
            upload(filename_map[uri[S3Path.KEY]], uri[S3Path.BUCKET], uri[S3Path.KEY])

        routeSpec = RouteSpec(
            [ReadingSpec(
                ReadingTypes.PREDICTION, 
                ReadingSpec.S3_FILES_FORMAT,
                pred_readings
            )], 
            name
        )

        print('saving readings to route database')
        route = self.api.save_route(routeSpec, user_id)

        return route

    def get_readings(
        self, 
        filenames: List[str],
        key: str,
        bucket: str, 
        read_gps_file: str, 
    ): 
        img_readings = []
        points = []

        filename_map = {}

        for filename in filenames:
            s3_filename = f'{key}/{filename.split("/")[-1]}'
            filename_map[s3_filename] = filename
            extension = s3_filename.split('.')[-1]
            file_portion = s3_filename.split('/')[-1]

            if extension == self.IMG_EXT:               
                img_readings.append(entry_from_file(bucket, s3_filename))
            elif file_portion == "GPS.txt":
                points.extend(txt_to_points(read_gps_file(filename)))
                print(points)
            else:
                print('unrecognized file in s3 bucket: ', s3_filename)

        return points, img_readings, filename_map
