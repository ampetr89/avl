DROP TABLE if exists osm.line
;

CREATE TABLE osm.line
(
    gid serial NOT NULL primary key,
    osm_id bigint,
    access character varying(11) COLLATE pg_catalog."default",
    aerialway character varying(15) COLLATE pg_catalog."default",
    aeroway character varying(32) COLLATE pg_catalog."default",
    amenity character varying(7) COLLATE pg_catalog."default",
    area character varying(32) COLLATE pg_catalog."default",
    barrier character varying(14) COLLATE pg_catalog."default",
    bicycle character varying(10) COLLATE pg_catalog."default",
    brand character varying(32) COLLATE pg_catalog."default",
    bridge character varying(3) COLLATE pg_catalog."default",
    boundary character varying(14) COLLATE pg_catalog."default",
    building character varying(11) COLLATE pg_catalog."default",
    covered character varying(3) COLLATE pg_catalog."default",
    culvert character varying(32) COLLATE pg_catalog."default",
    cutting character varying(3) COLLATE pg_catalog."default",
    disused character varying(3) COLLATE pg_catalog."default",
    embankment character varying(32) COLLATE pg_catalog."default",
    foot character varying(11) COLLATE pg_catalog."default",
    harbour character varying(32) COLLATE pg_catalog."default",
    highway character varying(14) COLLATE pg_catalog."default",
    historic character varying(5) COLLATE pg_catalog."default",
    horse character varying(7) COLLATE pg_catalog."default",
    junction character varying(10) COLLATE pg_catalog."default",
    landuse character varying(32) COLLATE pg_catalog."default",
    layer character varying(2) COLLATE pg_catalog."default",
    leisure character varying(4) COLLATE pg_catalog."default",
    lock character varying(3) COLLATE pg_catalog."default",
    man_made character varying(17) COLLATE pg_catalog."default",
    military character varying(32) COLLATE pg_catalog."default",
    motorcar character varying(7) COLLATE pg_catalog."default",
    name character varying(51) COLLATE pg_catalog."default",
    "natural" character varying(8) COLLATE pg_catalog."default",
    oneway character varying(10) COLLATE pg_catalog."default",
    operator character varying(46) COLLATE pg_catalog."default",
    population character varying(32) COLLATE pg_catalog."default",
    power character varying(32) COLLATE pg_catalog."default",
    place character varying(13) COLLATE pg_catalog."default",
    railway character varying(14) COLLATE pg_catalog."default",
    ref character varying(26) COLLATE pg_catalog."default",
    religion character varying(32) COLLATE pg_catalog."default",
    route character varying(14) COLLATE pg_catalog."default",
    service character varying(16) COLLATE pg_catalog."default",
    shop character varying(7) COLLATE pg_catalog."default",
    sport character varying(32) COLLATE pg_catalog."default",
    surface character varying(13) COLLATE pg_catalog."default",
    toll character varying(32) COLLATE pg_catalog."default",
    tourism character varying(6) COLLATE pg_catalog."default",
    "tower:type" character varying(32) COLLATE pg_catalog."default",
    tracktype character varying(32) COLLATE pg_catalog."default",
    tunnel character varying(16) COLLATE pg_catalog."default",
    water character varying(5) COLLATE pg_catalog."default",
    waterway character varying(14) COLLATE pg_catalog."default",
    wetland character varying(32) COLLATE pg_catalog."default",
    width character varying(3) COLLATE pg_catalog."default",
    wood character varying(32) COLLATE pg_catalog."default",
    z_order double precision,
    way_area numeric,
    tags  text COLLATE pg_catalog."default",
    geom geometry(MultiLineString,4326) 
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE osm.line
    OWNER to postgres;