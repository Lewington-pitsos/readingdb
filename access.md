# Access Patterns

According to AWS, you should design your DynamoDB schema based on the kind of access patterns you will be using. This document is an attempt to clarify what these access patterns are currently, and what they will be in future.

## Future Access Patterns

### Get all Routes Associated with a data access group

A data access group roughly corresponds to a real life organization or client.

**Load:** This will occur once, or maybe a few times the user logs in. There will probably be less than 100 routes per org returned by the server at any one time (as older ones will be filtered out).

**Implications** A data access group ID should be part of the primary key of a table containing all Route items.

### Get all Readings Associated with a Route

**Load:** At the moment this occurs once or maybe a few times per user session, as we load all readings at once. As the number of readings grows beyond 50,000, loading them all at once will be too expensive. As a result, we will need to start loading these readings incrementally (as the user gets closer to each reading), which could mean multiple queries per minute.

**Implications** The primary key of the Readings table should include a RouteID. We might also require some time-based or location based secindary keys so that we avoid loading readings not relevent to the user every 15 seconds or so.

### Get the data access group of the current user

**Load**: Once per session, a single item's worth of data.

**Implications**: Could simply be stored as its own table. Could be stored in a "misc" table which holds many low-load items, such as user-related data.

### Save New Prediction Readings**

Annotators will save their predictions to the database.

**Load**: a few items multiple times a minute, or 1000+ items all at once.

**Implications**: ???

