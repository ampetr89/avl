# avl
A web app for visualizing AVL data analysis

This project hits the [WMATA real time bus location API](https://developer.wmata.com/docs/services/54763629281d83086473f231/operations/5476362a281d830c946a3d68) at intervals of 5 seconds, weekdays during the morning and evening peak periods. The API reports a timestamp and the latitude and longitude of the vehicles, their trip_id (which ties to WMATA's static GTFS data), when the trip started, and the vehicle_id. The response also contain how delayed or ahead of schedule each bus currently is:

> Deviation, in minutes, from schedule. Positive values indicate that the bus is running late while negative ones are for buses running ahead of schedule.



The API results are stored in an Amazon Postgres database. Each trip "run" (a unique combination of the GTFS trip_id, trip_start_time, and vehicle_id) are matched to the underlying road network (OpenStreetMap). In other words, each lon/lat pair of bus coordinates is snapped to the street that it was travelling on.

- I make use of  a shortcut here. Since all of the buses travel along known routes, which are provided in the static GTFS file, I only need to do map matching on the static GTFS shape. 
- Then when I get raw position data from the API, I simply match each point to the closest road segment out of the segments that have already been matched for that route.

By having the coordinates (and more importantly the deviation) tied to a road segment id, it is possible to determine which road segments do the most harm to bus delay. The idea is to make an interactive visualization to show these results. At the moment, the front end is under development, but show a map with road segments colored by a metric related to on time performance, a list of the worst roads, and possible a panel where the bus trajectories on a particular road could be visualized.

The directories in this repo correspond to the following tasks:

* public: The front end code (Angular)

* server: The back end code (Node js)

* load

  * positions: Responsible for calling the WMATA API and storing the results

  * gtfs: Read in the static WMATA GTFS file

  * layer: Exploring the possibility of creating a custom Mapbox layer using just 
    "bus streets." (in development)

  * match: Match the GTFS route shapes to the road network. Also responsible for matching raw gps data from the API to the pre-matched road segments.

  * osm: loads OpenStreetMap roads to allow for visualization of the results

    ​

