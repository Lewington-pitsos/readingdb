import botocore
import boto3
import os
import json

def upload_fixtures(bucket: str, fixtures_dir: str, metadata_file: str) -> None:
    with open(metadata_file, "r") as f:
        metadata_json = json.load(f)

    client = boto3.client("s3")
    fixtures_paths = [
        os.path.join(path,  filename)
        for path, _, files in os.walk(fixtures_dir)
        for filename in files
    ]

    for path in fixtures_paths:
        key = os.path.relpath(path, fixtures_dir)
        print(key)
        client.upload_file(
            Filename=path, 
            Bucket=bucket, 
            Key=key,
            ExtraArgs=metadata_json[key] 
        )

def create_bucket(
    current_dir: str, 
    region_name: str, 
    access_key: str, 
    secret_key: str, 
    bucket_name: str,
):
    client = boto3.client(
        "s3",
        region_name=region_name,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        )
    try:
        s3 = boto3.resource(
            "s3",
            region_name=region_name,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            )
        s3.meta.client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError:
        pass
    else:
        err = "{bucket} should not exist.".format(bucket=bucket_name)
        raise EnvironmentError(err)        
    
    client.create_bucket(
        Bucket=bucket_name,  
        CreateBucketConfiguration={
            'LocationConstraint': region_name
        }
    )
    fixtures_dir = os.path.join(current_dir, "test_data/s3_fixtures")
    metadata_file = os.path.join(current_dir, "test_data/s3_metadata.json")
    upload_fixtures(bucket_name, fixtures_dir, metadata_file)  

def teardown_s3_bucket(
    region_name: str, 
    access_key: str, 
    secret_key: str, 
    bucket_name: str
):
    s3 = boto3.resource(
        "s3",
        region_name=region_name,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    bucket = s3.Bucket(bucket_name)
    for key in bucket.objects.all():
        key.delete()
    bucket.delete()