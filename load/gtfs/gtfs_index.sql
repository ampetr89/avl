
create index idx_shape on gtfs.shapes(shape_id)
;

create index idx_trips on gtfs.trips(shape_id);