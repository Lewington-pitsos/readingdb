# Database Objects

A description of some of the key objects that will be stored in our database.

## Reading

This is the fundimental unit of data, it represents a single instance of data from the real world being captured and stored.

## Layer

An arbitrary group of readings. Layers will be used to allow users to attend to or exclude groups of readings. For example, users are most likely most interested in the most up-to-date readings  for any geographic point, so it makes sense to have a layer which only includes these. 

Users may also want to share some of their readings with other users, layers allow this to happen as a user can aggregate the readings they want to share under a layer and then simply share that layer.

## Org

Represents an organization, which might be a client, an annotator or someone who we are demoing to. Organizations will often own multiple users. They can also be the source of multiple routes.