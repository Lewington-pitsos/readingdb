# Schema Design

## Primary Key

Geohash @ around 100x100 meters

## Secondary Key

ReadingType + Layer + ReadingID

Nothing too fancy.

## Indices

Global Index - RouteID - All Fields
Global Index - ImageHash - All Fields
Global Index - Geohash @ 4x4 meters - All Fields

