import json
import os
import boto3
from botocore.credentials import _local_now

def download_json_files(bucket: str, prefix: str, local_dir: str) -> None:
    bucket = boto3.resource("s3").Bucket(bucket)
    objects = bucket.objects.filter(Prefix=prefix)
    keys = [obj.key for obj in objects if obj.key.endswith(".json")]
    local_paths = [os.path.join(local_dir, key) for key in keys]   
    for key, local_path in zip(keys, local_paths):
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        bucket.download_file(key, local_path)