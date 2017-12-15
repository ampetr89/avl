drop table if exists way_deviation_change
;

create table way_deviation_change
    AS
select *, end_deviation - start_deviation  as deviation_change
from
(select run_id, way_id, 
  deviation as start_deviation, 
  lead(deviation) over (partition by run_id, way_id order by datetime) as end_deviation,
 start_of_way
 from 
(select run_id , way_id, deviation, datetime,
 row_number() over (partition by run_id, way_id order by datetime) as start_of_way,
 row_number() over (partition by run_id, way_id order by datetime desc) as end_of_way
from bus_position_match
 where way_id is not null
) as a
where start_of_way = 1 or end_of_way = 1
) as b
where start_of_way = 1
;

select wa