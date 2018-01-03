drop table if exists etl.matched_ways_endpoints
;

create table etl.matched_ways_endpoints
    as
select way_id, shape_id, edge_seq_num,
   ST_X(ST_startPoint(the_geom)) as start_lon, ST_y(ST_startPoint(the_geom)) as start_lat,
   ST_X(ST_endPoint(the_geom)) as end_lon, ST_y(ST_endPoint(the_geom)) as end_lat
from gtfs.matched_ways 
;

create index idx_matched_ways_endpoints on etl.matched_ways_endpoints(way_id);
create index idx_matched_ways_endpoints__start on etl.matched_ways_endpoints(start_lon, start_lat);
create index idx_matched_ways_endpoints__end on etl.matched_ways_endpoints(end_lon, end_lat);


----------


drop table if exists osm.road_points
;


create table osm.road_points 
    AS
select way_id, the_geom, ST_x(the_geom) as lon, ST_y(the_geom) as lat, path[1] - 1 as line_num, path[2] - 1 as point_num
from
(select way_id, (ST_dumpPoints(the_geom)).geom as the_geom, (ST_dumpPoints(the_geom)).path as path
from osm.roads 
) as a
;

create index idx_road_points  on osm.road_points(way_id);
create index idx_road_points__geom on osm.road_points(lon, lat)
;
----


drop table if exists osm.road_segments
;


create table osm.road_segments
  AS
select way_id,
    point_num, 
    lead(point_num) over (partition by way_id order by point_num) as next_point_num,
    ST_makeline(the_geom, lead(the_geom) over (partition by way_id order by point_num) ) as the_geom
    
from osm.road_points 
;

create index idx_road_segments on osm.road_segments(way_id, point_num)
    ;

----

drop table if exists gtfs.matched_ways_segments
;
create table gtfs.matched_ways_segments
as
select *
from (
select shape_id, edge_seq_num, a.way_id, 
  start_lon, start_lat, end_lon, end_lat,
  b1.line_num as start_line_num, b1.point_num as start_point_num, 
  row_number() over (partition by shape_id, edge_seq_num order by abs(a.start_lat - b1.lat) + abs(a.start_lon - b1.lon)) as r1,
   
  b2.line_num as end_line_num, b2.point_num as end_point_num,
  row_number() over (partition by shape_id, edge_seq_num order by abs(a.end_lat - b2.lat) + abs(a.end_lon - b2.lon)) as r2
from etl.matched_ways_endpoints as a
left join osm.road_points as b1
 on a.way_id = b1.way_id 
 and abs(a.start_lat - b1.lat) < 0.0001
 and abs(a.start_lon - b1.lon) < 0.0001 
left join osm.road_points as b2
 on a.way_id = b2.way_id 
 and abs(a.end_lat - b2.lat) < 0.0001
 and abs(a.end_lon - b2.lon) < 0.0001
) as x
where (r1 = 1 and r2 = 1) or start_lon is null or start_lat is null
;

create index idx_matched_ways_segments on gtfs.matched_ways_segments(shape_id, edge_seq_num)
;
----


/*
update bus_position_match set  start_point_num = NULL, end_point_num = NULL;


update bus_position_match as a 
 set start_point_num = b.start_point_num, end_point_num = b.end_point_num
from gtfs.matched_ways_segments as b
where a.way_id = b.way_id
and  a.shape_id = b.shape_id
and a.edge_seq_num = b.edge_seq_num
 ;
*/