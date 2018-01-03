drop table if exists bus_position_match_segment
;

create table bus_position_match_segment
as

select run_id, datetime, a.way_id, point_num, deviation, the_geom
from bus_position_match as a  
join osm.road_segments as b  
 on b.way_id = a.way_id 
 and (b.point_num between a.start_point_num and a.end_point_num
     or 
     b.point_num between a.end_point_num and a.start_point_num)
; 
----


drop table if exists way_deviation_change
;

create table way_deviation_change
    AS
select *, end_deviation - start_deviation  as deviation_change
from
(select run_id, way_id, start_point_num, end_point_num,
  shape_id, edge_seq_num,
  deviation as start_deviation, 
  lead(deviation) over (partition by run_id, way_id order by datetime) as end_deviation,
 start_of_way
 from 
(select run_id , way_id, start_point_num, end_point_num, 
    shape_id, edge_seq_num,
    deviation, datetime,
 row_number() over (partition by run_id, way_id, start_point_num, end_point_num order by datetime) as start_of_way,
 row_number() over (partition by run_id, way_id, start_point_num, end_point_num order by datetime desc) as end_of_way
from bus_position_match
 where way_id is not null
 and datetime between '2017-12-13 17:00:00' and  '2017-12-13 19:00:00'  /***time filter***/
) as a
where start_of_way = 1 or end_of_way = 1
) as b
where start_of_way = 1
;



select a.way_id, start_point_num, end_point_num, avg_deviation_change, n_runs, ST_SetSRID(ST_makeline(ST_makepoint(lon, lat)), 4326) as the_geom
from 
 (select way_id, start_point_num, end_point_num, round(avg(deviation_change)::decimal,2) as avg_deviation_change, count(*) as n_runs
  from way_deviation_change 
  where deviation_change is not null
  group by 1,2,3 having count(*) > 1 and avg(deviation_change) > 0
 ) as a
join osm.road_points as b 
 on a.way_id = b.way_id
 and b.point_num between a.start_point_num and a.end_point_num
group by 1,2,3,4,5
 order by avg_deviation_change desc
 ;





/*******
problem using edges is that the same street segment is used in multiple shapes,
but would be treated as different edges
***** */
drop table if exists edge_deviation_change
;

create table edge_deviation_change
    AS
select *, end_deviation - start_deviation  as deviation_change
from
(select run_id, way_id, shape_id, edge_seq_num, 
  deviation as start_deviation, 
  lead(deviation) over (partition by run_id,  shape_id, edge_seq_num order by datetime) as end_deviation,
 start_of_way
 from 
(select run_id, way_id, shape_id, edge_seq_num, deviation, datetime,
 row_number() over (partition by run_id, shape_id, edge_seq_num order by datetime) as start_of_way,
 row_number() over (partition by run_id,  shape_id, edge_seq_num order by datetime desc) as end_of_way
from bus_position_match
 where way_id is not null
) as a
where start_of_way = 1 or end_of_way = 1
) as b
where start_of_way = 1
;



select a.shape_id, a.edge_seq_num, avg_deviation_change, n_runs, b.the_geom
from 
 (select shape_id, edge_seq_num, round(avg(deviation_change)::decimal,2) as avg_deviation_change, count(*) as n_runs
  from edge_deviation_change 
  where deviation_change is not null
  group by 1,2 having count(*) > 10 and having avg(deviation_change) > 0) as a
join gtfs.matched_ways as b 
 on a.shape_id = b.shape_id
 and a.edge_seq_num = b.edge_seq_num
 ;