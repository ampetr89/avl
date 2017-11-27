from pandas import read_sql
from db import Db

dbconn = Db().conn

"""
TODO: make a small table with just the routes, and a child table route_direction
"""
def get_routes():
	routes = read_sql("""
		select routeid
		from bus_position
		group by 1
		""", dbconn)
	return list(routes['routeid'])

def get_gps(routeId):
	coords = read_sql("""
		select datetime, ST_asgeojson(ST_flipcoordinates(ST_makepoint(lon,lat))) as geojson
		from bus_position
		where scheduled_trip_id = '929987020'
		""".format(routeId), dbconn)
	return coords.to_dict('records')

def get_gtfs_shape(route_name):
	# shape simplify tolerance = 0.0001
	shapes = read_sql("""
	 select a.*, 
	 ST_asgeojson(ST_FlipCoordinates(the_geom)) as geojson
	  /* ST_asgeojson(ST_FlipCoordinates(ST_Simplify(the_geom, .0001, true))) as geojson*/
	 from( 
		select route_short_name, direction_id, trip_headsign, shape_id, count(*) as n_trips
		from gtfs.routes as r 
		join gtfs.trips as t
		 on r.route_id = t.route_id
		 and r.route_short_name = '{}'
		group by 1,2,3,4) as a
        
    join gtfs.shape_line as s
     on a.shape_id = s.shape_id
       
		""".format(route_name), dbconn)

	return shapes.to_dict('records')

def get_matched_shape(route_name):
	shapes = read_sql("""select ST_AsGEOJSON(ST_FlipCoordinates(
		  ST_makeline(ST_makepoint(lon, lat) order by shape_seq_num))) as geojson
	from gtfs.matched_shape 
	where shape_id = '760'
	""", dbconn)

	return shapes.to_dict('records')