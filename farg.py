import argparse

from readingdb.digester import Digester
from readingdb.endpoints import *

parser = argparse.ArgumentParser()
parser.add_argument('bucket', help='the bucket where the zipped file is kept', type=str)
parser.add_argument('key', help='the object key for the zipped file', type=str)
parser.add_argument('region', help='the region where the data resources (s3 and dynamodb) are stored', type=str, default='ap-southeast-2')
parser.add_argument('name', help='the name of the new route', type=str, default=None)

args = parser.parse_args()

def perform_unzip(bucket: str, key: str, name: str=None):
    print('initializing unzipper')
    z = Digester(DYNAMO_ENDPOINT, region_name=args.region)

    print('unzipping')
    z.process(bucket, key, name)
    print('unzipping and saving complete')

perform_unzip(args.bucket, args.key, args.name)