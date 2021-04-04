from enum import Enum

class RouteStatus(Enum):
    UPLOADED = 1
    PREDICTING = 2
    COMPLETE = 3