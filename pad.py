# import json

# file_name = "readingdb/test_data/tst_imgs.json"

# with open(file_name, "r") as f:
#     entries = json.load(f)

# keys = [
#     "LongCrack",
#     "LatCrack",
#     "CrocodileCrack",
#     "Pothole",
#     "Lineblur",
# ]

# for e in entries:
#     entities = []
#     for k in keys:
#         entities.append({
#             "Name": k,
#             "Confidence": e["Reading"][k + "Confidence"],
#             "Present": e["Reading"]["Is" + k + "Fault"]
#         })
#         del e["Reading"][k + "Confidence"]
#         del e["Reading"]["Is" + k + "Fault"]

#     e['Reading']["Entities"] = entities

# with open(file_name, "w") as f:
#     json.dump(entries, f, indent="    ")

# -----------------------------------------------------------------------------

# from readingdb.endpoints import DYNAMO_ENDPOINT, TEST_DYNAMO_ENDPOINT
# from readingdb.db import DB
# import time

# db = DB(DYNAMO_ENDPOINT)

# db.teardown_reading_db()
# time.sleep(10)
# db.create_reading_db()

# -----------------------------------------------------------------------------

# from readingdb.api import API
# from readingdb.routespec import RouteSpec
# import json

# api = API("https://dynamodb.ap-southeast-2.amazonaws.com")

# with open("readingdb/test_data/ftg_route.json") as f:
#     route_json = json.load(f) 
# api.save_route(RouteSpec.from_json(route_json), "99bf4519-85d9-4726-9471-4c91a7677925")

# with open("readingdb/test_data/gps_img_route.json") as f:
#     route_json = json.load(f) 

# api.save_route(RouteSpec.from_json(route_json), "99bf4519-85d9-4726-9471-4c91a7677925")

# with open("readingdb/test_data/ftg_20_route.json") as f:
#     route_json = json.load(f) 

# api.save_route(RouteSpec.from_json(route_json), "99bf4519-85d9-4726-9471-4c91a7677925")


# -----------------------------------------------------------------------------

import boto3

# Probably won't need a public IP

client = boto3.client('ecs')

resp = client.run_task(
    networkConfiguration={
        'awsvpcConfiguration': {
            'subnets': ['subnet-0567cac0229946232'],
            'securityGroups': ['sg-fe12c9b7'],
            'assignPublicIp': 'ENABLED'
        },
    },
    launchType="FARGATE",
    cluster="arn:aws:ecs:ap-southeast-2:950765595897:cluster/unzipper-cluster",
    taskDefinition="arn:aws:ecs:ap-southeast-2:950765595897:task-definition/unzipper-fargate:6",
    overrides={
        "containerOverrides": [
            {
                "name": "unzipper", 
                "command":  ["python", "farg.py", "mobileappsessions172800-main", "public/route_2021_04_08_15_14_46_792.zip", "ap-southeast-2"]
            }
        ]
    }
)
     
print(resp)