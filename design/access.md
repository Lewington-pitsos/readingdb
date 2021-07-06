# Access Patterns

According to AWS, you should design your DynamoDB schema based on the kind of access patterns you will be using. This document is an attempt to clarify what these access patterns are currently, and what they will be in future.

## Summary

### Users
- All Access groups for the current user
- All Routes associated with a data access group (annotating)
- All readings associated with a route (when annotating)
- All readings within a geographic area and assoaicted with an access group
- All readings associated with a given image (when saving annotations)
- Get particular route (for deletion/update)

### Routes
- All Routes associated with an access group

### Readings

- All Readings associated with a large geographic area and access group
- All Readings of a certain type in the same geographic area and access group as the current reading


### Aggregates

- All Aggregates associated with a large geographic area and access group
- All Aggregates in the same access group as a given reading

### Get all Routes Associated with a data access group

A data access group roughly corresponds to a real life organization or client.

**Load:** This will occur once, or maybe a few times the user logs in, and only if the user is using the annotation feautures. There will probably be less than 100 routes per org returned by the server at any one time (as older ones will be filtered out).

**Implications** A data access group ID should be part of the primary key of a table containing all Route items.

### Get all Readings Inside a Geographic Box

**Load:** This will happen many times during a session as the user pans around and zooms the map. Each new pan means a new box and each new zoom means a different resolution of faults. This will basically be happening constantly. This is necessairy to avoid long wait times as faults that are not needed (i.e. literally any faults outside that box) are loaded.

**Implications** We need some kind of geographic caching for each reading.

### Get the data access group of the current user

**Load**: Once per session, a single item's worth of data.

**Implications**: Could simply be stored as its own table. Could be stored in a "misc" table which holds many low-load items, such as user-related data.

### Load readings that correspond to predictions being saved

Annotators will save their predictions (for images) to the database. This will require querying the predictions that already exist for the relevent images to check if any of these predictions are overriding existing predictions. E.g. the same annotator makes a correction to an earlier prediction.

**Load**: About 3 per second, saved in batches of 100 or 200, or up to 10,000 saved all at once.

**Implications**: It is not economical to load all readings every time 100 or so get saved. Basically we will need to add an image hash to each reading and make this a secondary key.

### Load readings that correspond to the user's screen.

When the user looks at the map, they will want to look at the readings in that area. They an only access readings that belong to routes that are within the proper access group though.

**Load**: very high, this is kind of the main thing the app will do other than load aggregates. There will be thousands of readings per screen.


### Load unprotected readings that need replacing

When a new reading R1 is saved, if there exist unprotected readings in the same location as R1 (so, within x meters) and those readings have older timestamps than R1 and belong to the same access group as the uploader, those readings must be shunted to cold-storage.

**Load**: multiple uploads of tens of thousands of readings each day, each reading must perform this check

**Implications**: the reading's sort key should include some flag specifying whether it is protected or not.

**Implications**: The process should presumably be 
(1) user loads all routes that it is able to access 
(2) user specifies some geographic bounds (probably multiple "squares" that together make up the entire map)
(3) The reading table is queried over geohash and route id

### Load aggregates that correspond to the user's screen.

Same as above, but only hundreds of readings per screen.

### Mark Readings for Annotation

The user selectes a number of aggregates. Each reading associated with any of these aggregates
must now be annotated. 

**Load**: At most once per upload with all the readings for that upload. At least once per year.

**Implications**: We need a new entity called an "annotation job". All it needs to do is store readingids and will be deleted frequently. It must be associated with a particular data access group. The sort key of reach reading must include the routeID so we can reconstruct readings into the order of capture (for easier annotation).

### Update Aggregates

Whenever a new route is uploaded, any aggregate that overlaps any of the readings in that new route must be updated. Presumably will simply delete all these aggregates and re-build using the new readings.

**Load**: once per upload, probably hundreds, probably < 1000 aggregates will need to be deleted and re-created or at least updated.

**Implications**: Aggregates will need to have a geohash as part of their primary key