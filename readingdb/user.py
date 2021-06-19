from boto3.resources.model import Identifier
from readingdb.constants import AdjKeys, UserKeys
from typing import Any, Dict, List

def get_key_type(id: str) -> str:
    return id.split(AdjKeys.DIVIDER)[0]

def get_key_value(id: str) -> str:
    return id.split(AdjKeys.DIVIDER)[-1]

class User():
    @classmethod
    def from_raw(cls, data: List[Dict[str, Any]]) -> None:
        formatted = {}

        access_groups = []

        for row in data:
            pk_type = get_key_type(row[AdjKeys.PK])
            sk_type = get_key_type(row[AdjKeys.SK])
            sk_value = get_key_value(row[AdjKeys.SK])
            if pk_type == UserKeys.USER_SUFFIX and sk_type == UserKeys.ORG_SUFFIX:
                if UserKeys.ORG_SUFFIX in formatted:
                    raise ValueError('Multiple orgs given for user data', data)
                formatted[UserKeys.ORG_SUFFIX] = {
                    UserKeys.ORG_NAME: row[UserKeys.ORG_NAME],
                    UserKeys.ORG_ID: sk_value
                }
            elif pk_type == UserKeys.USER_SUFFIX and sk_type == UserKeys.GROUP_SUFFIX:
                pass
            elif pk_type == UserKeys.USER_SUFFIX and sk_type == UserKeys.USER_SUFFIX:
                if UserKeys.SUB in formatted:
                    raise ValueError('Multiple user IDs in user data', data)
                formatted[UserKeys.SUB] = sk_value
            elif pk_type == UserKeys.GROUP_SUFFIX and sk_type == UserKeys.GROUP_SUFFIX:
                access_groups.append({
                    UserKeys.AG_NAME: row[UserKeys.AG_NAME],
                    UserKeys.AG_ID: sk_value        
                })
            else:
                raise ValueError(f'Unexpected kind found in row:', row)

        formatted[UserKeys.ACCESS_GROUPS] = access_groups


        return cls(formatted)

    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data
    
    def json(self) -> Dict[str, Any]:
        return self.data