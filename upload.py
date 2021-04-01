import argparse
import json
from readingdb.uploader import Uploader
from readingdb.auth import Auth

parser = argparse.ArgumentParser(description="Uploads given data to the Faultnet Database")
parser.add_argument("routepath", type=str, help="A path to a file containing all the data for a route")
parser.add_argument("-u", "--username", type=str, help="The AWS cognito login username")
parser.add_argument("-p", "--password", type=str, help="The AWS cognito login password")
parser.add_argument("-c", "--clientid", type=str, help="The AWS cognito client id")
parser.add_argument("-a", "--authfile", type=str, help="A path to a file containing authentication details")

args = parser.parse_args()

if __name__ == "__main__":
    auth = Auth(args.username, args.password, args.clientid)

    with open(args.routepath, "r") as f:
        route = json.load(f)

    uploader = Uploader(auth)

    uploader.upload(route)