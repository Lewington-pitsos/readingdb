# Process For Saving A Route

1. Upload all files
2. Notify the backend that a save has occurred, provide user sub
3. Fetch the Organizaton for the given user
4. Fetch the default group for that organization
5. Generate a new layer for this route and add it to the default group
6. Save the route, adding all readings to that layer