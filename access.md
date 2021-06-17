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

### Admin
- All Routes


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

