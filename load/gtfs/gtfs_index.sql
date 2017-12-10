alter table gtfs.stops add column the_geom geometry(point, 4326)
;
update gtfs.stops set the_geom = ST_SETSRID(st_makepoint(stop_lon, stop_lat), 4326)
;
create index gdx_stops on gtfs.stops using GIST(the_geom)
;

alter table gtfs.shapes add column the_geom geometry(point, 4326)
;
update gtfs.shapes set the_geom = ST_SETSRID(st_makepoint(shape_pt_lon, shape_pt_lat), 4326)
;
create index gdx_shapes on gtfs.shapes using GIST(the_geom)
;


create index idx_shape on gtfs.shapes(shape_id)
;

create index idx_trips on gtfs.trips(shape_id);