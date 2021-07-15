# Schema Design For DynamoDB Items

Our general strategy is based on what the guy talks about in this video: https://www.youtube.com/watch?v=BnDKD_Zv0og

## Reading

### Primary Key

Geohash @ around 100x100 meters

### Secondary Key

ReadingID

### Indices

Global Index - RouteID - All Fields
Global Index - ImageHash - All Fields
Global Index - Geohash @ 4x4 meters - All Fields



| Item           | Primary Key  | Sort Key     |
| :------------- | :----------: | -----------: |
|  Route         | Route        | And Again    |
| You Can Also   | Put Pipes In | Like this \| |



## AccessGroup

This will be modelled exclusively using inverted indices

### Inverted Indices

User + AccessGroup
Layer + AccessGroup

### Query Logic

1. find all access groups for user
2. find all layers for each access group