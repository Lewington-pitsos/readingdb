# Road Segments

## Why Include Road Segments?

Analysts are used to dealing with segments of road. E.g. the segment of Liddard Street between Rathmines Road and Peterson Avenue is in really bad condition.

Also, we need a way of aggregating fault data when the user takes a very high-level view of the network. If we load invidiaual readings at this scale the user will have to wait a long time while this huge (> 100mb) quantity of data is transferred.

So, we need some kind of aggregate entity to store in the backend that gets fetched first. Ideally each aggregate entity should cover 1000 individal entities, but at least 100. This way we get to reduce the quantity of data transferred by 100x. 

In general, whenever the user finishes saving a number of readings, we will have to

- locate the aggregates that might be effected
- recalculate their statuses
- save them again

Basically, we would have to use google maps Places api. When snapping points to roads (which we will do for every point) the returned points are all associated with a 'placeId'. The placeIds returned all refer to a road segment place, which in general seem to refer to streches of road between two intersections. These make reasonable candidates for aggregates (usually 20-100 points per segment), and are clearly deterministic. 