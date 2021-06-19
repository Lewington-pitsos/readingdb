from boto3.resources.model import Identifier
from readingdb.constants import AdjKeys, UserKeys
from typing import Any, Dict, List

def get_type(id: str) -> str:
    return id.split(AdjKeys.DIVIDER)[0]

def get_value(id: str) -> str:
    return id.split(AdjKeys.DIVIDER)[-1]

class User():
    @classmethod
    def from_raw(cls, data: List[Dict[str, Any]]) -> None:
        formatted = {
            UserKeys.ACCESS_GROUPS: [],
            UserKeys.ORG_SUFFIX: {},
        }

        for row in data:
            kind = get_type(row[AdjKeys.SK])
            identifier = get_value(row[AdjKeys.SK])
            if kind == UserKeys.ORG_SUFFIX:
                formatted[UserKeys.ORG_SUFFIX] = {
                    UserKeys.ORG_NAME: row[UserKeys.ORG_NAME],
                    UserKeys.ORG_ID: identifier
                }
            elif kind == UserKeys.GROUP_SUFFIX:
                formatted[UserKeys.ACCESS_GROUPS].append(identifier)
            elif kind == UserKeys.USER_SUFFIX:
                if UserKeys.SUB in formatted:
                    raise ValueError('Multiple user IDs in user data', data)

                formatted[UserKeys.SUB] = identifier
            else:
                raise ValueError(f'Unexpected kind found in row:', row)

        return cls(formatted)

    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data
    
    def json(self) -> Dict[str, Any]:
        return self.data