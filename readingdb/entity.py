from typing import Dict, Any

from readingdb.constants import *
from readingdb.clean import *

class Entity():
    def __init__(self, name: str, confidence: float, present: bool, severity: float=1.0) -> None:
        self.name = name
        self.confidence: float = confidence
        self.present: bool = present
        self.severity = severity

    def encode(self) -> Dict[str, Any]:
        return {
            Constants.ENTITY_NAME: self.name,
            Constants.CONFIDENCE: encode_as_float(self.confidence),
            Constants.PRESENT: encode_bool(self.present),
            Constants.SEVERITY: encode_as_float(self.severity)
        }