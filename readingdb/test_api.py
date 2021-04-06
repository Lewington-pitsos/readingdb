import os
import tempfile
import unittest
import boto3
import botocore
from moto import mock_s3
from readingdb.download_json import download_json_files

MY_BUCKET = "my_bucket"
MY_PREFIX = "mocks"

def _upload_fixtures(bucket: str, fixtures_dir: str) -> None:

    client = boto3.client("s3")
    fixtures_paths = [
        os.path.join(path,  filename)
        for path, _, files in os.walk(fixtures_dir)
        for filename in files
    ]

    for path in fixtures_paths:
        key = os.path.relpath(path, fixtures_dir)
        client.upload_file(Filename=path, Bucket=bucket, Key=key)

@mock_s3
class TestDownloadJsonFiles(unittest.TestCase):
    region_name = "ap-southeast-2"
    access_key = "fake_access_key"
    secret_key = "fake_secret_key"

    def setUp(self):
        client = boto3.client(
            "s3",
            region_name=self.region_name,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            )
        try:
            s3 = boto3.resource(
                "s3",
                region_name=self.region_name,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                )
            s3.meta.client.head_bucket(Bucket=MY_BUCKET)
        except botocore.exceptions.ClientError:
            pass
        else:
            err = "{bucket} should not exist.".format(bucket=MY_BUCKET)
            raise EnvironmentError(err)        
        
        client.create_bucket(
            Bucket=MY_BUCKET,  
            CreateBucketConfiguration={
                'LocationConstraint': self.region_name
            }
        )
        current_dir = os.path.dirname(__file__)
        fixtures_dir = os.path.join(current_dir, "test_data/s3_fixtures")
        _upload_fixtures(MY_BUCKET, fixtures_dir)    
    
    def tearDown(self):
        s3 = boto3.resource(
            "s3",
            region_name=self.region_name,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )
        bucket = s3.Bucket(MY_BUCKET)
        for key in bucket.objects.all():
            key.delete()
        bucket.delete()
    
    def test_download_json_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            download_json_files(MY_BUCKET, MY_PREFIX, tmpdir)
            mock_folder_local_path = os.path.join(tmpdir, MY_PREFIX)
            self.assertTrue(os.path.isdir(mock_folder_local_path))
            result = os.listdir(mock_folder_local_path)
            desired_result = ["file.json", "apple.json"]
            self.assertCountEqual(result, desired_result)