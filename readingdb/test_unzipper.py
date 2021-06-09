from copy import Error
from logging import error
import os

from botocore.retries import bucket
from readingdb.route import Route
import tempfile
import unittest
from moto import mock_s3, mock_sqs
import uuid

from readingdb.download_json import download_json_files
from readingdb.api import API
from readingdb.endpoints import *
from readingdb.unzipper import Unzipper
from readingdb.tutils import *

@mock_s3
@mock_sqs
class TestUnzipper(unittest.TestCase):
    region_name = 'ap-southeast-2'
    access_key = 'fake_access_key'
    secret_key = 'fake_secret_key'
    bucket_name = 'my_bucket'
    test_prefix = 'mocks'

    def setUp(self):
        self.current_dir = os.path.dirname(__file__)
        create_bucket(
            self.current_dir, 
            self.region_name, 
            self.access_key, 
            self.secret_key, 
            self.bucket_name
        )

        self.api = API(TEST_DYNAMO_ENDPOINT) 
        self.api.create_reading_db()

        self.sqs = boto3.client('sqs')
        self.queue_name = str(uuid.uuid1())
        self.sqs_url = self.sqs.create_queue(
            QueueName=self.queue_name
        )['QueueUrl']
        
    
    def tearDown(self):
        teardown_s3_bucket(
            self.region_name,
            self.access_key,
            self.secret_key,
            self.bucket_name
        )

        self.api.teardown_reading_db()
        self.sqs.delete_queue(QueueUrl=self.sqs_url)

    def test_mocking_works(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            download_json_files(self.bucket_name, self.test_prefix, tmpdir)
            mock_folder_local_path = os.path.join(tmpdir, self.test_prefix)
            self.assertTrue(os.path.isdir(mock_folder_local_path))
            result = os.listdir(mock_folder_local_path)
            desired_result = ['file.json', 'apple.json']
            self.assertCountEqual(result, desired_result)

    def test_unzipper_adds_to_queue(self):
        z = Unzipper(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name, sqs_url=self.sqs_url)
        route: Route = z.process(self.bucket_name, 'mocks/route_2021_04_07_17_14_36_709.zip')
        readings = self.api.all_route_readings(route.id)

        self.assertEqual(len(readings), 39)

        msg = self.sqs.receive_message(
            QueueUrl=self.sqs_url,
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=0,
            WaitTimeSeconds=0
        )['Messages'][0]

        # washiwashi is the userid in the metadata of mocks/route_2021_04_07_17_14_36_709.zip
        self.assertEqual(f'washiwashi,{route.id}', msg['Body'])

    def test_unzipper_uploads_route_with_unix_timestamps(self):
        z = Unzipper(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name, sqs_url=self.sqs_url)
        route: Route = z.process(self.bucket_name, 'mocks/route_1621394080578.zip')
        readings = self.api.all_route_readings(route.id)

        self.assertEqual(len(readings), 98)

        s3 = boto3.resource('s3')
        bucket = s3.Bucket(self.bucket_name)

        bucket_objects = []

        for my_bucket_object in bucket.objects.all():
            bucket_objects.append(my_bucket_object.key)

        self.assertEqual(set(bucket_objects), set([
            'mocks/route_1621394080578/img_1621394116949-64.jpg',
            'mocks/route_1621394080578/img_1621394086919-10.jpg',
            'mocks/route_1621394080578/img_1621394090196-16.jpg',
            'mocks/route_1621394080578/img_1621394111922-55.jpg',
            'mocks/route_1621394080578/img_1621394119101-68.jpg',
            'mocks/route_1621394080578/img_1621394108064-48.jpg',
            'mocks/route_1621394080578/img_1621394104677-42.jpg',
            'mocks/route_1621394080578/img_1621394096866-28.jpg',
            'mocks/route_1621394080578/img_1621394086301-9.jpg',
            'mocks/route_1621394080578/img_1621394097997-30.jpg',
            'mocks/route_1621394080578/img_1621394105186-43.jpg',
            'mocks/route_1621394080578/img_1621394109696-51.jpg',
            'mocks/route_1621394080578/img_1621394110825-53.jpg',
            'mocks/route_1621394080578/img_1621394114692-60.jpg',
            'mocks/route_1621394080578/img_1621394116329-63.jpg',
            'mocks/route_1621394080578/img_1621394117970-66.jpg',
            'mocks/route_1621394080578/img_1621394117460-65.jpg',
            'mocks/route_1621394080578/img_1621394115818-62.jpg',
            'mocks/route_1621394080578/img_1621394095844-26.jpg',
            'mocks/route_1621394080578/img_1621394097486-29.jpg',
            'mocks/file.json',
            'mocks/route_1621394080578/img_1621394107443-47.jpg',
            'mocks/route_1621394080578/img_1621394121877-73.jpg',
            'mocks/route_1621394080578/img_1621394111335-54.jpg',
            'mocks/route_1621394080578/img_1621394112431-56.jpg',
            'mocks/route_1621394080578/img_1621394113560-58.jpg',
            'mocks/route_1621394080578/img_1621394119718-69.jpg',
            'mocks/route_1621394080578/img_1621394105805-44.jpg',
            'mocks/route_1621394080578/img_1621394110206-52.jpg',
            'mocks/route_1621394080578/img_1621394089685-15.jpg',
            'mocks/route_1621394080578/img_1621394115202-61.jpg',
            'mocks/route_1621394080578/img_1621394099126-32.jpg',
            'mocks/route_1621394080578/img_1621394103031-39.jpg',
            'mocks/route_1621394080578/img_1621394109081-50.jpg',
            'mocks/route_1621394080578/img_1621394099746-33.jpg',
            'mocks/route_1621394080578/img_1621394101902-37.jpg',
            'mocks/route_1621394080578/img_1621394113050-57.jpg',
            'mocks/route_1621394080578/img_1621394120230-70.jpg',
            'mocks/route_1621394080578/img_1621394084047-5.jpg',
            'mocks/route_1621394080578/img_1621394100771-35.jpg',
            'mocks/route_1621394080578/img_1621394121366-72.jpg',
            'mocks/route_1621394080578/img_1621394102412-38.jpg',
            'mocks/route_1621394080578/img_1621394091942-19.jpg',
            'mocks/route_1621394080578/img_1621394094089-23.jpg',
            'mocks/route_1621394080578/img_1621394118589-67.jpg',
            'mocks/route_1621394080578/img_1621394090813-17.jpg',
            'mocks/route_1621394080578/img_1621394089068-14.jpg',
            'mocks/route_1621394080578/img_1621394104166-41.jpg',
            'mocks/route_1621394080578/img_1621394088049-12.jpg',
            'mocks/route_1621394080578/img_1621394103542-40.jpg',
            'mocks/route_1621394080578/img_1621394085792-8.jpg',
            'mocks/route_1621394080578/GPS.txt',
            'mocks/apple.json',
            'mocks/route_1621394080578/img_1621394087430-11.jpg',
            'mocks/route_1621394080578/img_1621394108573-49.jpg',
            'mocks/route_1621394080578/img_1621394083537-4.jpg',
            'mocks/route_1621394080578/img_1621394092962-21.jpg',
            'mocks/route_1621394080578/img_1621394093580-22.jpg',
            'mocks/route_1621394080578/img_1621394106316-45.jpg',
            'mocks/route_1621394080578/img_1621394083027-3.jpg',
            'mocks/route_1621394080578/img_1621394088560-13.jpg',
            'mocks/route_2021_04_07_17_14_36_709.zip',
            'mocks/route_1621394080578/img_1621394085174-7.jpg',
            'mocks/route_1621394080578/img_1621394091322-18.jpg',
            'mocks/route_1621394080578/img_1621394101390-36.jpg',
            'mocks/route_1621394080578/img_1621394120852-71.jpg',
            'mocks/route_1621394080578/img_1621394092452-20.jpg',
            'mocks/route_1621394080578/img_1621394106935-46.jpg',
            'mocks/route_1621394080578/img_1621394096354-27.jpg',
            'mocks/route_1621394080578/img_1621394095228-25.jpg',
            'mocks/route_1621394080578/img_1621394114070-59.jpg',
            'mocks/route_1621394080578/img_1621394098616-31.jpg',
            'mocks/route_1621394080578/img_1621394084664-6.jpg',
            'mocks/route_1621394080578/img_1621394094712-24.jpg',
            'mocks/route_1621394080578/img_1621394100257-34.jpg',
        ]))

    def test_unzipper_uploads(self):
        z = Unzipper(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name, sqs_url=self.sqs_url)
        route: Route = z.process(self.bucket_name, 'mocks/route_2021_04_07_17_14_36_709.zip')
        readings = self.api.all_route_readings(route.id)

        self.assertEqual(len(readings), 39)

        s3 = boto3.resource('s3')
        bucket = s3.Bucket(self.bucket_name)

        bucket_objects = []

        for my_bucket_object in bucket.objects.all():
            bucket_objects.append(my_bucket_object.key)

        self.assertEqual(set(bucket_objects), set([
            'mocks/apple.json', 
            'mocks/file.json',
            'mocks/route_1621394080578.zip',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_54_981-41.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_47_617-20.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_45_848-15.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_54_702-40.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_45_467-14.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_49_037-24.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_46_922-18.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_46_230-16.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_51_150-30.jpg',
            'mocks/route_2021_04_07_17_14_36_709/GPS.txt',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_48_689-23.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_52_198-33.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_51_500-31.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_50_469-28.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_49_773-26.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_53_244-36.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_48_308-22.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_51_849-32.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_52_547-34.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_50_798-29.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_54_284-39.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_50_055-27.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_55_404-42.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_47_928-21.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_54_006-38.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_46_544-17.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_47_234-19.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_49_386-25.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_53_587-37.jpg',
            'mocks/route_2021_04_07_17_14_36_709/2021_04_07_17_14_52_899-35.jpg',
        ]))
        
    def test_unzipper_uploads_with_route_name(self):
        z = Unzipper(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name, sqs_url=self.sqs_url)
        route: Route = z.process(self.bucket_name, 'mocks/route_2021_04_07_17_14_36_709.zip', 'bennet court')

        readings = self.api.all_route_readings(route.id)
        self.assertEqual(len(readings), 39)
        self.assertEqual('bennet court', route.name)

    def test_unzipper_uploads_local_files(self):
        z = Unzipper(TEST_DYNAMO_ENDPOINT, bucket=self.bucket_name, sqs_url=self.sqs_url)

        pth = 'readingdb/test_data/route_imgs/route_2021_04_07_17_14_36_709/'
        files = [pth + f for f in os.listdir(pth)]

        route = z.process_local(
            'some_user_id',
            'route_2021_04_29_14_15_34_999',
            self.bucket_name,
            files,
            'test_route'
        )

        readings = self.api.all_route_readings(route.id)
        self.assertEqual(len(readings), 28)

        s3 = boto3.resource('s3')
        bucket = s3.Bucket(self.bucket_name)
        bucket_objects = []
        for my_bucket_object in bucket.objects.all():
            bucket_objects.append(my_bucket_object.key)
        self.assertEqual(32, len(bucket_objects))