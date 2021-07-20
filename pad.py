from readingdb.endpoints import DYNAMO_ENDPOINT
from readingdb.api import API

api = API(DYNAMO_ENDPOINT)

rs = api.all_route_readings('c6496334-b434-11eb-ac0e-0242e489f95d')