import time

import argparse

from readingdb.unzipper import Unzipper
from readingdb.endpoints import *

parser = argparse.ArgumentParser()
parser.add_argument("bucket", help="the bucket where the zipped file is kept", type=str)
parser.add_argument("key", help="the object key for the zipped file", type=str)
parser.add_argument("region", help="the region where the data resources (s3 and dynamodb) are stored", type=str, default="ap-southeast-2")

args = parser.parse_args()

def perform_unzip(bucket, key):
    print("initializing unzipper")
    z = Unzipper(DYNAMO_ENDPOINT, region_name=args.region)

    print("unzipping")
    z.process(bucket, key)
    print("unzipping and saving complete")

perform_unzip(args.bucket, args.key)