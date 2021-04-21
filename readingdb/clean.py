from decimal import Decimal

def encode_float(value: float) -> Decimal:
    return Decimal(str(value))

def encode_bool(value: bool) -> int:
    return 1 if value else 0

def decode_float(value: Decimal) -> float:
    return float(value)

def decode_bool(value: int) -> bool:
    return value == 1
