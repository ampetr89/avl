drop table if exists etl.bus_position
;

create table etl.bus_position(
 DateTime TIMESTAMP,
 deviation FLOAT,
 direction_num INT,
 direction_text VARCHAR(50),
 lat FLOAT,
 lon FLOAT,
 route_short_name VARCHAR(10),
 trip_end_time TIMESTAMP,
 trip_headsign VARCHAR(100),
 scheduled_trip_id BIGINT,
 trip_start_time TIMESTAMP,
 vehicle_id VARCHAR(10),
 the_geom geometry(point, 4326)
 );


drop table if exists public.bus_position
;
create table public.bus_position(
 run_id not null,
 DateTime TIMESTAMP,
 deviation FLOAT,
 direction_num INT,
 direction_text VARCHAR(50),
 lat FLOAT,
 lon FLOAT,
 route_short_name VARCHAR(10),
 trip_end_time TIMESTAMP,
 trip_headsign VARCHAR(100),
 scheduled_trip_id BIGINT,
 trip_start_time TIMESTAMP,
 vehicle_id VARCHAR(10),
 the_geom geometry(point, 4326),
 PRIMARY KEY(scheduled_trip_id,trip_start_time,vehicle_id,datetime)
 );

create index idx_bus_position__id on bus_position(run_id)
;
create index idx_bus_position__trip on bus_position(scheduled_trip_id)
;
create index idx_bus_position__datetime on bus_position(datetime)
;

CREATE INDEX gix_bus_position ON bus_position USING GIST (the_geom);
;



drop table if exists public.bus_position_match
;
create table public.bus_position_match(
	run_id int, -- FK to bus_position
    DateTime timestamp,-- FK to bus_position
    deviation float, 

    way_id bigint, 
    begin_heading float, 
    end_heading float, 
    weighted_grade float, 
    speed float, 
    road_class varchar(30), 
    length float,

	shape_id varchar(100),
	edge_seq_num int,
    /*edge_geom geometry(linestring, 4326),*/
    dist_meters decimal,
    /*dist_rank int,*/

    /* derived columns */
    interp int,
    route_id int, 
    trip_dist_pct decimal,
    headway decimal -- requires interpolating times / distances.....
)
;
create index idx_bus_position_match__id on bus_position_match(run_id, datetime)
;

create index idx_bus_position_match__edge on bus_position_match(shape_id, edge_seq_num)
;

drop table if exists etl.bus_position_match__route
;
create table etl.bus_position_match__route(
    run_id int, -- FK to bus_position
    datetime timestamp, -- FK to bus_position
    deviation float, 
    
    way_id bigint, 
    begin_heading float, 
    end_heading float, 
    weighted_grade float, 
    speed float, 
    road_class varchar(30), 
    length float,

    shape_id varchar(100),
    edge_seq_num int,
    /*edge_geom geometry(linestring, 4326),*/
    dist_meters decimal,
    dist_rank int ,
    interp int
);
/*create index gdx_bus_position_match__route 
      on etl.bus_position_match__route (route_id, trip_dist_pct)*/


drop table if exists gtfs.trip_run_vehicle
;
create table gtfs.trip_run_vehicle(
  id serial primary key,
  scheduled_trip_id BIGINT, 
  trip_start_time timestamp, 
  vehicle_id varchar(10)
 );

create index idx_trip_run_vehicle on gtfs.trip_run_vehicle(scheduled_trip_id, trip_start_time)
    ;

"""
update bus_position as a
set run_id  = b.id
from gtfs.trip_run_vehicle as b
where a.scheduled_trip_id = b.scheduled_trip_id
and a.trip_start_time = b.trip_start_time
and a.vehicle_id = b.vehicle_id
"""