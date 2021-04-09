from typing import Dict, Any

from readingdb.constants import *
from readingdb.clean import *

class Entity():
    def __init__(self, name: str, confidence: float, present: bool) -> None:
        self.name = name
        self.confidence: float = confidence
        self.present: bool = present

    def encode(self) -> Dict[str, Any]:
        return {
            EntityKeys.NAME: self.name,
            EntityKeys.CONFIDENCE: encode_float(self.confidence),
            EntityKeys.PRESENT: encode_bool(self.present),
        }