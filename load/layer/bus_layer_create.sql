drop table if exists public.bus_layer
;


create table public.bus_layer
as
select * from osm.roads
where way_id in (select way_id from gtfs.matched_ways group by 1)
;