GEOHASH_PRECISION = 6
REGION_NAME = 'ap-southeast-2'

LAT = 'lat'
LNG = 'lng'

ANNOTATOR_PREFERENCE = [
    '2f11b71a-cecf-40b8-ab6b-8c73e4254b26'
]

class Constants():
    # Generic
    PARTITION_KEY = 'PK'
    SORT_KEY = 'SK'

    # User
    USER_ID = 'UserID'
    GROUPS = 'DataAccessGroups'
    
    # Database
    READING_TABLE_NAME = 'Readings2'
    ORG_TABLE_NAME = 'Org'
    PAGINATION_KEY_NAME = 'PaginationKey'
    USER_TABLE_NAME = 'Annotators'

    # Org Table Partitions
    READING_PK = 'Reading'
    ROUTE_PK = 'Route'
    LAYER_PK = 'Layer'
    ORG_PK = 'Org'
    USER_PK = 'User'
    GROUP_PK = 'Group'

    # AccessGroups
    GROUP_NAME = 'GroupName'

    # Reading Types
    PREDICTION = 'PredictionReading'
    IMAGE_TYPES = [PREDICTION]

    # Reading Keys
    GEOHASH = 'Geohash'
    ROUTE_ID = 'RouteID'
    READING_ID = 'ReadingID'
    TYPE = 'Type'
    READING = 'Reading'
    TIMESTAMP = 'Timestamp'
    LAYER_ID = 'LayerID'
    READING_NAME = 'Readings'
    

    # Positional Reading Keys
    LATITUDE = 'Latitude'
    LONGITUDE = 'Longitude'
    PLACE_ID = 'PlaceID'

    # Image Reading Keys
    FILENAME = 'ImageFileName'
    URI = 'S3Uri'
    PRESIGNED_URL = 'PresignedURL'

    # Prediction Reading Keys
    ENTITIES = 'Entities'
    ANNOTATOR_ID = 'AnnotatorID'
    ANNOTATION_TIMESTAMP = 'AnnotationTimestamp'

    # Route Keys
    USER_ID = 'UserID'
    NAME = 'RouteName'
    SAMPLE_DATA = 'SampleData'
    STATUS = 'RouteStatus'
    TIMESTAMP = 'Timestamp'
    LAST_UPDATED = 'LastUpdated'
    ROUTE_HASHES = 'Geohashes'

    # S3 Path
    BUCKET = 'Bucket'
    KEY = 'Key'

    # Entity Keys
    ENTITY_NAME = 'Name'
    CONFIDENCE = 'Confidence'
    PRESENT = 'Present'
    SEVERITY = 'Severity'

    # Layer Keys
    LAYER_NAME = 'LayerName'
    LAYER_READINGS = 'LayerReadings'

    # Org Keys
    ORG_NAME = 'OrgName'
    ORG_GROUP = 'OrgGroup'

    # Data Access Group
    GROUP_NAME = 'GroupName'
    GROUP_ID = 'GroupID'
    

DEFAULT_ANNOTATOR_NAME = 'LoukaSean'
DEFAULT_ANNOTATOR_ID = '99bf4519-85d9-4726-9471-4c91a7677925'
FAUX_ANNOTATOR_ID = '3f01d5ec-c80b-11eb-acfa-02428ee80691'
DEFAULT_LAYER_ID = 'f9ddebe1-e054-11eb-b74d-04d9f584cf20'