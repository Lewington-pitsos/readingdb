from enum import IntEnum

class RouteStatus(IntEnum):
    UPLOADED = 1
    PREDICTING = 2
    COMPLETE = 3