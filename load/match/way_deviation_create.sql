drop table if exists way_deviation
;
create table way_deviation 
AS
 select scheduled_trip_id, trip_date, way_id, 
 ST_union(edge_geom order by edge_seq_num) as way_geom,
 max(way_start_deviation) as way_start_deviation, max(way_end_deviation) as way_end_deviation,
  max(way_end_deviation) -  max(way_start_deviation) deviation_change
from (
    select scheduled_trip_id, datetime::date as trip_date, way_id, 
    edge_seq_num, edge_geom,
     case when row_number() over (partition by scheduled_trip_id, datetime::date, way_id order by datetime ) = 1 
        then deviation else NULL end as way_start_deviation,
     case when row_number() over (partition by scheduled_trip_id, datetime::date, way_id order by datetime desc) = 1 
        then deviation else NULL end as way_end_deviation
     from  bus_position_match
    where way_id is not null
    ) as a
group by 1,2,3