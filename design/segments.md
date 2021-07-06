# Road Segments

## Why Include Road Segments?

Analysts are used to dealing with segments of road. E.g. the segment of Liddard Street between Rathmines Road and Peterson Avenue is in really bad condition.

Also, we need a way of aggregating fault data when the user takes a very high-level view of the network. If we load invidiaual readings at this scale the user will have to wait a long time while this huge (> 100mb) quantity of data is transferred.

So, we need some kind of aggregate entity to store in the backend that gets fetched first. Ideally each aggregate entity should cover 1000 individal entities, but at least 100. This way we get to reduce the quantity of data transferred by 100x. 

In general, whenever the user finishes saving a number of readings, we will have to

- locate the aggregates that might be effected
- recalculate their statuses
- save them again

Our options are:

### polylines with arbitrary start and end points

#### Pro

- Segments relate to road defects rather than arbitrary points

#### Con

- Segments are always chainging


### A mix of a geohashing grid with 100-300 m squares and google maps geo roads.

I.e. a segment = all the road points for google roads road X that lie inside the square Y.


#### Pro 

- Easy + Cheap to tell which segment a reading belongs to

#### Con

- Grid will mean some segments of road are tiny (e.g. the last 20 meters of Fullard road is in square c1)