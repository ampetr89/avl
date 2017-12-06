drop table if exists gtfs.matched_point
;

create table gtfs.matched_point(
	shape_id varchar(100),
	shape_pt_sequence smallint,
	lon float, 
	lat float,
	distance_along_edge float,
	distance_from_trace_point float,
	type varchar(25),
	edge_index bigint

);

drop table if exists gtfs.matched_shape
;

create table gtfs.matched_shape(
	shape_id varchar(100),
	lon float,
	lat float,
	shape_seq_num bigint
);

create index idx_matched_shape on gtfs.matched_shape(shape_id, shape_seq_num)
;

drop table if exists gtfs.matched_ways
;
create table gtfs.matched_ways(
	shape_id varchar(100),
	edge_seq_num bigint,
	names text,

	way_id bigint,
	sign text,
	begin_heading float,
	end_heading float,
	begin_shape_index bigint,
	end_shape_index bigint,
		
	weighted_grade float,
	id bigint,
	speed int,
	length float,
	road_class varchar(30),

	the_geom geometry(linestring, 4326)
);

CREATE INDEX gix_matched_ways ON gtfs.matched_ways USING GIST (the_geom);
;
create index idx_matched_ways ON gtfs.matched_ways(shape_id, edge_seq_num);
;

drop table if exists etl.matched_ways
;
create table etl.matched_ways(
	shape_id varchar(100),
	edge_seq_num bigint,
	names text,

	way_id bigint,
	sign text,
	begin_heading float,
	end_heading float,
	begin_shape_index bigint,
	end_shape_index bigint,
		
	weighted_grade float,
	id bigint,
	speed int,
	length float,
	road_class varchar(30)
);

create index idx_matched_ways on etl.matched_ways(shape_id, begin_shape_index, end_shape_index)
;
create index idx_matched_ways2 on etl.matched_ways(shape_id, edge_seq_num)
;


create table etl.matched_ways_geom(
	shape_id varchar(100),
	edge_seq_num bigint,
	the_geom geometry(linestring, 4326)
)
;
create index idx_matched_ways_geom on etl.matched_ways_geom(shape_id, edge_seq_num)
;