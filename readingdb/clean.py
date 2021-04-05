import json
from decimal import Decimal
from os import read

import numpy as np

def encode_float(value: float) -> Decimal:
    return Decimal(str(value))

def encode_bool(value: bool) -> int:
    return 1 if value else 0

def decode_float(value: Decimal) -> float:
    return float(value)

def decode_bool(value: int) -> bool:
    return value == 1

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return super(CustomJSONEncoder, self).encode(bool(obj))
        if isinstance(obj, Decimal):
            return int(obj)

        return super(CustomJSONEncoder, self).default(obj)