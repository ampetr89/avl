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

create index idx_bus_position__trip on bus_position(scheduled_trip_id)
;
create index idx_bus_position__datetime on bus_position(datetime)
;

CREATE INDEX gix_bus_position ON bus_position USING GIST (the_geom);
;



drop table if exists public.bus_position_match
;
create table public.bus_position_match(
	datetime timestamp ,
	scheduled_trip_id bigint,
    route_short_name varchar(50),
    direction_text varchar(50),
    trip_headsign varchar(100),
	lon float, 
	lat float,
	deviation float,
	vehicle_id varchar(10),
	shape_id varchar(100),
	edge_seq_num int

)