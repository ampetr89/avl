drop table if exists bus_position_temp
;
create table bus_position_temp
as 
select * from (
select *, row_number() over (partition by datetime order by 1) as dup_num
from bus_position 
where scheduled_trip_id = 929987020
)  as a where dup_num = 1
;

create index gidx_bus_position_temp on bus_position_temp using gist (the_geom) 
;

/*insert into bus_position_match(datetime, scheduled_trip_id)*/
select * from 
(select datetime, scheduled_trip_id, 
  route_short_name, direction_text, trip_headsign,
  lon as gps_lon, lat as gps_lat, deviation, vehicle_id, shape_id, edge_seq_num,
  edge_geom as the_geom,
  row_number() over (partition by scheduled_trip_id, datetime order by dist_meters asc) as dist_rank
from 
(
 select a.*, 
     b.shape_id, edge_seq_num, c.the_geom as edge_geom,
     ceiling(ST_distance(a.the_geom::geography, c.the_geom::geography)) as dist_meters

    from bus_position_temp as a  
    join gtfs.trips as b
     on a.scheduled_trip_id = b.scheduled_trip_id 
    left join gtfs.matched_ways as c
     on b.shape_id = c.shape_id
     and ST_Dwithin(a.the_geom, c.the_geom, .0005) 

) as a ) as b
where dist_rank = 1
;