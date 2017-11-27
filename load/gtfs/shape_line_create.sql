
drop table if exists gtfs.shape_line
;
create table gtfs.shape_line
as 
select shape_id, 
  ST_SetSRID(ST_makeline(
  	 ST_makepoint(shape_pt_lon, shape_pt_lat)
  	 order by shape_pt_sequence
  	 ) , 4326) as the_geom,
  null::geometry(linestring) as the_geom_simple

from gtfs.shapes
group by 1  
; /* 4 seconds */


update gtfs.shape_line
	 set the_geom_simple = ST_simplify(the_geom,.0001) 
;
