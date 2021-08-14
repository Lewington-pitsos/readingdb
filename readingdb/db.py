import uuid
from readingdb.format import route_sort_key
from readingdb.utils import timestamp
import time
from typing import Any, Callable, Dict, List, Set, Tuple

import boto3
from boto3.dynamodb.conditions import Key

from readingdb.clean import *
from readingdb.reading import PredictionReading, ddb_to_dict, Reading, geohash_partition_key
from readingdb.route import Route
from readingdb.constants import *

class DB():
    ITEM_KEY = 'Items'
    LAST_EVAL_KEY = 'LastEvaluatedKey'

    def __init__(
        self, 
        url, 
        resource_name='dynamodb',
        region_name='ap-southeast-2', 
        config=None,
        max_page_readings=1800,
    ):
        self.db = boto3.resource(
            resource_name, 
            region_name=region_name,
            endpoint_url=url, 
            config=config,
        )

        # DynamoDB only returns 1MB of data in a single query
        # use paginator on queries that stand a chance of returning
        # > 1MB of data.
        self.client = self.db.meta.client
        self.paginator = self.client.get_paginator('query')
        self.scan_paginator = self.client.get_paginator('scan')
        self.max_page_readings = max_page_readings

        self.reading_table = self.db.Table(Constants.READING_TABLE_NAME)
        self.org_table = self.db.Table(Constants.ORG_TABLE_NAME)

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- GENERAL ------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def __paginate_table(
        self, 
        table_name: str,
        decode_fn: Callable[[Dict[str, Any]], Any],
        query_key: str = None,
        query_value: str = None,
    )-> Any:
        if query_key is not None:
            pg = self.paginator.paginate(
                TableName=table_name,
                KeyConditionExpression=Key(query_key).eq(query_value)
            )
        else:
            pg = self.scan_paginator.paginate(
                TableName=table_name,
            )

        items = []
        for page in pg:
            for item in page[self.ITEM_KEY]:
                decode_fn(item)
                items.append(item)

        return items

    def all_tables(self) -> List[Any]:
        return list(self.db.tables.all())

    def create_reading_db(
        self, 
    ) -> Tuple[Any, Any]:
        self.reading_table = self.__make_reading_table()
        self.org_table = self.__make_org_table()
        return (self.reading_table, self.org_table)

    def teardown_reading_db(self) -> None:
        self.__delete_table(Constants.READING_TABLE_NAME)
        self.__delete_table(Constants.ORG_TABLE_NAME)
    
    def __delete_table(self, table_name) -> None:
        self.db.Table(table_name).delete()

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- ROUTE --------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def remove_route(self, route_id: str):
        self.org_table.delete_item(
            Key={
                Constants.PARTITION_KEY: Constants.ROUTE_PK,
                Constants.SORT_KEY: route_sort_key(route_id)
            }
        )

    def put_route(self, route: Route): 
        return self.org_table.put_item(Item=route.item_data())

    def get_route(self, route_id: str) -> Dict[str, Any]:
        response = self.org_table.query(
            KeyConditionExpression=
                Key(Constants.PARTITION_KEY).eq(Constants.ROUTE_PK) &
                Key(Constants.SORT_KEY).eq(route_sort_key(route_id))
        )

        if len(response[self.ITEM_KEY]) < 1:
            return None

        item = response[self.ITEM_KEY][0]
        Route.decode_item(item)

        return item

    def route_geohashes(self, route_id: str) -> Set[str]:
        route = self.get_route(route_id)

        if route is None:
            return set()

        return set(route[Constants.ROUTE_HASHES])

    def routes_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        groups = self.groups_for_user(user_id)
        routes = self.all_routes()

        return [r for r in routes if r[Constants.GROUP_ID] in groups] 

    def all_routes(self) -> List[Dict[str, Any]]:
        response = self.org_table.query(
            KeyConditionExpression=Key(Constants.PARTITION_KEY).eq(Constants.ROUTE_PK)
        )

        return [Route.decode_item(item) for item in response[self.ITEM_KEY]]

    def update_route_name(self, route_id: str, name: str) -> None:
        r: Dict[str, Any] = self.get_route(route_id)

        if r[Constants.NAME] != name:        
            self.org_table.update_item(
                Key={
                    Constants.PARTITION_KEY: Constants.ROUTE_PK,
                    Constants.SORT_KEY: route_sort_key(route_id)
                },
                UpdateExpression=f'set {Constants.NAME} = :r, {Constants.LAST_UPDATED} = :l',
                ExpressionAttributeValues={
                    ':r': name,
                    ':l': int(time.time())
                },
            )

    def set_route_status(self, route_id: str, status: int) -> None:
        r: Dict[str, Any] = self.get_route(route_id)

        if r[Constants.STATUS] != status:
            self.org_table.update_item(
                Key={
                    Constants.PARTITION_KEY: Constants.ROUTE_PK,
                    Constants.SORT_KEY: route_sort_key(route_id)
                },
                UpdateExpression=f'set {Constants.STATUS} = :r, {Constants.LAST_UPDATED} = :l',
                ExpressionAttributeValues={
                    ':r': status,
                    ':l': int(time.time())
                },
            )

    def __make_org_table(self):
        return self.db.create_table(
            TableName=Constants.ORG_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName':  Constants.PARTITION_KEY,
                    'KeyType': 'HASH'  
                },
                {
                    'AttributeName': Constants.SORT_KEY,
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': Constants.PARTITION_KEY,
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': Constants.SORT_KEY,
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 100,
                'WriteCapacityUnits': 100
            }
        )

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- READING ------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def put_readings(self, readings: List[PredictionReading]):
        with self.reading_table.batch_writer() as batch:
            for r in readings:
                batch.put_item(Item=r.item_data())

    def get_route_readings(self, route_id: str) -> List[Dict[str, Any]]:
        geohashes = self.route_geohashes(route_id)
        all_readings = []

        for geohash in geohashes:
            print(geohash)
            hash_readings = self.__paginate_table(
                Constants.READING_TABLE_NAME,
                ddb_to_dict,
                Constants.PARTITION_KEY,
                geohash_partition_key(geohash, Constants.PREDICTION),
            )
            all_readings.extend([r for r in hash_readings if r[Constants.ROUTE_ID] == route_id])
        
        return all_readings

    def geohash_readings(self, geohash: str, reading_type: str) -> List[Dict[str, Any]]:
        response = self.reading_table.query(
            KeyConditionExpression=Key(Constants.PARTITION_KEY).eq(geohash_partition_key(geohash, reading_type))
        )
        return response[self.ITEM_KEY]

    def put_reading(self, reading: PredictionReading):
        return self.reading_table.put_item(Item=reading.item_data())

    def delete_reading_items(self, readings: List[Dict[str, str]])-> None:
        for reading in readings:
            self.reading_table.delete_item(
                Key=Reading.get_key(reading)
            )

    def __make_reading_table(self):
        return self.db.create_table(
            TableName=Constants.READING_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': Constants.PARTITION_KEY,
                    'KeyType': 'HASH'  
                },
                {
                    'AttributeName': Constants.SORT_KEY,
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': Constants.PARTITION_KEY,
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': Constants.SORT_KEY,
                    'AttributeType': 'S'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 500,
                'WriteCapacityUnits': 500
            }
        )

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # --------------------------- LAYERS ------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def put_layer(
        self, 
        layer_id: str, 
        readings: List[Dict[str, Any]] = None,
        name:str=None
    ) -> str:
        if readings is not None:
            existing_readings = self.layer_readings([layer_id])
            existing_reading_ids = set()
            current_reading_ids = set()

            for reading in readings:
                current_reading_ids.add(reading[Constants.READING_ID])

            for reading in existing_readings:
                reading_id = reading[Constants.READING_ID]
                existing_reading_ids.add(reading_id)
                if reading_id not in current_reading_ids:
                    self.remove_reading_from_layer(layer_id, reading)

            for reading in readings:
                if reading[Constants.READING_ID] not in existing_reading_ids:
                    self.add_reading_to_layer(layer_id, reading)

        item = {
            Constants.PARTITION_KEY: Constants.LAYER_PK,
            Constants.SORT_KEY: self.__layer_sort_key(layer_id),
        }

        if name is not None:
            item[Constants.LAYER_NAME] = name

        self.org_table.put_item(Item=item)

        return layer_id

    def remove_readings_from_layer(self, layer_id: str, readings: List[Dict[str, Any]]):
        for reading in readings:        
            self.remove_reading_from_layer(layer_id, reading)

    def remove_reading_from_layer(self, layer_id: str, reading: Dict[str, Any]):
        self.org_table.delete_item(Key={
            Constants.PARTITION_KEY: self.__layer_reading_primary_key(layer_id),
            Constants.SORT_KEY: reading[Constants.READING_ID]
        })

    def add_readings_to_layer(self, layer_id:str, readings: List[Dict[str, Any]]) -> None:
        for reading in readings:
            self.add_reading_to_layer(layer_id, reading)

    def add_reading_to_layer(self, layer_id: str, reading: Dict[str, Any]):
        self.org_table.put_item(Item={
            Constants.PARTITION_KEY: self.__layer_reading_primary_key(layer_id),
            Constants.SORT_KEY: reading[Constants.READING_ID],
            Constants.READING_ID: reading[Constants.READING_ID],
            Constants.GEOHASH: reading[Constants.GEOHASH],
            Constants.READING_TYPE: reading[Constants.READING_TYPE],
        })

    def layer_ids_for_user(self, user_id: str):
        layer_ids = []

        group_ids = self.groups_for_user(user_id)
        for id in group_ids:
            layer_ids.extend(self.layer_ids_for_group(id))

        return layer_ids
    
    def layers_for_user(self, user_id:str) -> List[Dict[str, Any]]:
        layers = []

        group_ids = self.groups_for_user(user_id)
        for id in group_ids:
            layer_ids = self.layer_ids_for_group(id)

            print('layer ids', layer_ids)

            for layer_id in layer_ids:
                layers.append(self.get_layer(layer_id))        

        return layers

    def readings_for_layer_id(self, layer_id:str) -> List[Dict[str, Any]]:
        return self.layer_readings([layer_id])

    def layer_readings(self, layer_ids: str) -> List[Dict[str, Any]]:
        readings = []

        geohashes = set() 
        reading_ids = set()

        for layer_id in layer_ids:
            identifiers = self.__layer_reading_identifiers(layer_id)            

            for identifier in identifiers:
                geohashes.add(identifier[Constants.GEOHASH])
                reading_ids.add(identifier[Constants.SORT_KEY])

        for geohash in geohashes:
            geohash_readings = self.geohash_readings(geohash, Constants.PREDICTION)
            for geohash_reading in geohash_readings:
                if geohash_reading[Constants.READING_ID] in reading_ids:
                    readings.append(geohash_reading)
                    
        return readings

    def identifiers_for_layers(self, layer_ids: List[str]):
        all_identifiers = []

        for layer_id in layer_ids:
            all_identifiers.extend(self.__layer_reading_identifiers(layer_id))

        return all_identifiers

    def __layer_reading_identifiers(self, layer_id: str) -> Dict[str, Any]:
        resp = self.org_table.query(
            KeyConditionExpression=
                Key(Constants.PARTITION_KEY).eq(self.__layer_reading_primary_key(layer_id))
        )

        return resp[self.ITEM_KEY] 

    def get_layer(self, layer_id: str) -> Dict[str, Any]:
        response = self.org_table.query(
            KeyConditionExpression=
                Key(Constants.PARTITION_KEY).eq(Constants.LAYER_PK) &
                Key(Constants.SORT_KEY).eq(self.__layer_sort_key(layer_id))
        )

        if len(response[self.ITEM_KEY]) == 0:
            return None 
        
        return response[self.ITEM_KEY][0]

    def __layer_id_from_layer_data(self, layer_data: List[Dict[str, Any]]) -> str:
        return layer_data[Constants.SORT_KEY].split('#')[1]

    def __layer_sort_key(self, layer_id: str) -> str:
        return f'Layer#{layer_id}'

    def __layer_reading_primary_key(self, layer_id: str):
        return f'LayerReading#{layer_id}'
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # ---------------------------- GROUPS -----------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def put_group(self, group_id: str, name=None) -> None:
        item = {
            Constants.PARTITION_KEY: Constants.GROUP_PK,
            Constants.SORT_KEY: self.__group_key(group_id),
            Constants.GROUP_ID: group_id
        }

        if name is not None:
            item[Constants.GROUP_NAME] = name

        self.org_table.put_item(Item=item)

    def set_group_name(self, group_id:str, name:str) -> None:
        self.put_group(group_id, name)

    def get_group(self, group_id: str) -> Dict[str, Any]:
        resp = self.org_table.query(
            KeyConditionExpression=
                Key(Constants.PARTITION_KEY).eq(Constants.GROUP_PK) &
                Key(Constants.SORT_KEY).eq(self.__group_key(group_id))
        )

        return resp[self.ITEM_KEY][0]

    def user_add_group(self, user_id: str, group_id: str) -> None:
        self.org_table.put_item(Item={
            Constants.PARTITION_KEY: self.__user_group_pk(user_id),
            Constants.SORT_KEY: self.__group_key(group_id),
        })

    def user_remove_group(self, user_id: str, group_id: str) -> None:
        self.org_table.delete_item(Key={
            Constants.PARTITION_KEY: self.__user_group_pk(user_id),
            Constants.SORT_KEY: self.__group_key(group_id)
        })

    def group_add_layer(self, group_id: str, layer_id: str) -> None:
        self.org_table.put_item(Item={
            Constants.PARTITION_KEY: self.__group_key(group_id),
            Constants.SORT_KEY: self.__layer_group_pk(layer_id),
        })

    def group_remove_layer(self, group_id: str, layer_id: str) -> None:
        self.org_table.delete_item(Key={
            Constants.PARTITION_KEY: self.__group_key(group_id),
            Constants.SORT_KEY: self.__layer_group_pk(layer_id),
        })


    def groups_for_user(self, user_id: str) -> List[str]:
        response = self.org_table.query(KeyConditionExpression=
            Key(Constants.PARTITION_KEY).eq(self.__user_group_pk(user_id)))

        group_ids = []

        for item in response[self.ITEM_KEY]:
            group_ids.append(self.__id_from_key(item[Constants.SORT_KEY]))

        return group_ids

    def user_has_group(self, user_id: str, group_id: str) -> bool:
        response = self.org_table.query(KeyConditionExpression=
            Key(Constants.PARTITION_KEY).eq(self.__user_group_pk(user_id))
        )

        for item in response[self.ITEM_KEY]:
            if self.__id_from_key(item[Constants.SORT_KEY]) == group_id:
                return True
        
        return False

    def __user_group_pk(self, user_id: str) -> str:
        return f'UserGroup#{user_id}'
    
    def __id_from_key(self, agid: str) -> str:
        return agid.split("#")[-1]

    def layer_ids_for_group(self, group_id: str) -> str:
        response = self.org_table.query(
            KeyConditionExpression=
                Key(Constants.PARTITION_KEY).eq(self.__group_key(group_id))
        )

        layer_ids = []

        for item in response[self.ITEM_KEY]:
            layer_ids.append(self.__id_from_key(item[Constants.SORT_KEY]))
        
        return layer_ids

    def __layer_group_pk(self, layer_id: str) -> str:
        return f'LayerGroup#{layer_id}'

    def __group_key(self, acess_group_id: str) -> str:
        return f'Group#{acess_group_id}'

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # --------------------------- ORG ---------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def put_org(self, org_name:str, default_group_id: str = None) -> Dict[str, Any]:
        if default_group_id is None:
            default_group_id = str(uuid.uuid1())
        
        item = {
            Constants.PARTITION_KEY: Constants.ORG_PK,
            Constants.SORT_KEY: self.__org_sk(org_name),
            Constants.ORG_NAME: org_name,
            Constants.ORG_GROUP: default_group_id
        }

        self.org_table.put_item(Item=item)

        return item

    def get_orgs(self) -> List[Dict[str, Any]]:
        response = self.org_table.query(
            KeyConditionExpression=
                Key(Constants.PARTITION_KEY).eq(Constants.ORG_PK)
        )

        return response[self.ITEM_KEY]

    def get_org(self, org_name: str) -> Dict[str, Any]:
        response = self.org_table.query(
            KeyConditionExpression=
                Key(Constants.PARTITION_KEY).eq(Constants.ORG_PK) &
                Key(Constants.SORT_KEY).eq(self.__org_sk(org_name)),
        )

        if len(response[self.ITEM_KEY]) > 0:
            return response[self.ITEM_KEY][0]
        return None

    def __org_sk(self, org_id:str) -> str:
        return f'Org#{org_id}'

    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -------------------------- USER ---------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------
    # -----------------------------------------------------------------

    def user_data(self, org_name:str, user_id: str)-> Dict[str, Any]:
        response = self.org_table.query(
            KeyConditionExpression=
                Key(Constants.PARTITION_KEY).eq(self.__user_org_key(org_name)) &
                Key(Constants.SORT_KEY).eq(self.__user_sort_key(user_id))
        )

        return response[self.ITEM_KEY][0]

    def all_users(self, org_name:str) -> List[Dict[str, Any]]:
        resp = self.org_table.query(
            KeyConditionExpression=
                Key(Constants.PARTITION_KEY).eq(self.__user_org_key(org_name))
        )

        return resp[self.ITEM_KEY]

    def all_user_ids(self, org_name:str) -> List[str]: 
        user_ids = []
        response = self.org_table.query(
            KeyConditionExpression=
                Key(Constants.PARTITION_KEY).eq(self.__user_org_key(org_name))
        )

        for item in response[self.ITEM_KEY]:
            user_ids.append(item[Constants.USER_ID])

        return user_ids

    def put_user(self, org_name, user_id: str) -> None:       
        self.org_table.put_item(Item={
            Constants.PARTITION_KEY: self.__user_org_key(org_name),
            Constants.SORT_KEY: self.__user_sort_key(user_id),
            Constants.TIMESTAMP: timestamp(),
            Constants.USER_ID: user_id,
            Constants.ORG_NAME: org_name
        })

        org = self.get_org(org_name)

        self.user_add_group(user_id, org[Constants.ORG_GROUP])

    def __user_org_key(self, org_name: str) -> str:
        return f'Org#{org_name}'

    def __user_sort_key(self, user_id: str) -> str:
        return f'User#{user_id}'