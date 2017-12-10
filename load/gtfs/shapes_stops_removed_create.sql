drop table if exists gtfs.shapes_stops_removed
;

create table gtfs.shapes_stops_removed
As
select a.*
from gtfs.shapes as a
where not exists (
    select stop_lon, stop_lat
    from gtfs.stops as b, geog_conversion as c
    where ST_DWithin(a.the_geom, b.the_geom, 10*mrad)
)
;
