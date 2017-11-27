drop table if exists geog_conversion
;
create table geog_conversion as
 select m2lon, m2lat, 1/m2lon as lon2m, 1/m2lat as lat2m, null::decimal as mrad
 from (
     select ST_LENGTH(ST_makeline(ST_translate(o, 1, 0), o)::geography) as m2lon,
            ST_LENGTH(ST_makeline(ST_translate(o, 0, 1), o)::geography) as m2lat
     
     from
    (select ST_SETSRID(ST_makepoint(-77.0436967, 38.8996135), 4326) as o) as a 
) as b
/* confirmed here https://msi.nga.mil/MSISiteContent/StaticFiles/Calculators/degree.html*/
;

update geog_conversion set mrad = sqrt(lon2m^2 + lat2m^2)
;
select * from geog_conversion


/* -- '.0000152' = 1 deg of lon > 1 deg lat
-- examples:
 '2.30553815','2.65762167380566e-05'
'32.20273072','0.000301039864472555'
'22.10258989','0.000199160739104683'
'11.12317081','0.000128217402662322'
'50.40344025','0.000492576897554749' ==> 50 meters = .0005
*/