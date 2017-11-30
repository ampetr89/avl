import pandas as pd

#%%
import sys
sys.path.append('../')
from db import Db

db = Db()
dbconn = db.conn
pg = db.pg
cur = pg.cursor()


#%%

def match_gps(scheduled_trip_id, start_time, end_time):
  cur.execute('''
  drop table if exists bus_position_temp
  ''')

  cur.execute('''
  create table bus_position_temp
  as 
  select * from (
   select *, row_number() over (partition by datetime order by 1) as dup_num
   from bus_position 
   where scheduled_trip_id = %(scheduled_trip_id)s
   and datetime between %(start_time)s and %(end_time)s
  )  as a where dup_num = 1
  ''', {'scheduled_trip_id':scheduled_trip_id, 'start_time': start_time, 'end_time': end_time}
    )

  cur.execute('''
  create index gidx_bus_position_temp on bus_position_temp using gist (the_geom) 
    ''')
  pg.commit()

  cur.execute('''
  insert into bus_position_match(datetime, scheduled_trip_id, route_short_name, direction_text,
                                trip_headsign, gps_lon, gps_lat, deviation ,vehicle_id,
                                 way_id, begin_heading, end_heading, weighted_grade, speed_limit, road_class, length,
                                shape_id, edge_seq_num, edge_geom, dist_rank)
  select * from 
  (select datetime, scheduled_trip_id, 
    route_short_name, direction_text, trip_headsign,
    lon as gps_lon, lat as gps_lat, deviation, vehicle_id, 
    way_id, begin_heading, end_heading, weighted_grade, speed_limit, road_class, length,
    shape_id, edge_seq_num,
    edge_geom as the_geom,
    row_number() over (partition by scheduled_trip_id, datetime order by dist_meters asc) as dist_rank
  from 
  (
   select a.*, 
        c.way_id, c.begin_heading, c.end_heading, c.weighted_grade, c.speed as speed_limit, c.road_class, c.length,
       b.shape_id, edge_seq_num, c.the_geom as edge_geom,
       ceiling(ST_distance(a.the_geom::geography, c.the_geom::geography)) as dist_meters

      from bus_position_temp as a  
      join gtfs.trips as b
       on a.scheduled_trip_id = b.scheduled_trip_id 
      left join gtfs.matched_ways as c
       on b.shape_id = c.shape_id
       and ST_Dwithin(a.the_geom, c.the_geom, .0005) 

  ) as a ) as b
  where dist_rank = 1
  ''')
  pg.commit()

def get_trips(shape_id, start_time, end_time):
  """
  get the trips for the particular shape, only the ones that occured
  during the interval we care about and who have not already been matched
  """
  trips_to_match = pd.read_sql('''
   select scheduled_trip_id
    from gtfs.trips
     where shape_id = %(shape_id)s
      and scheduled_trip_id in (
          select scheduled_trip_id from bus_position 
         where datetime between %(start_time)s and %(end_time)s)
      and scheduled_trip_id not in (
          select scheduled_trip_id from bus_position_match 
         where datetime between %(start_time)s and %(end_time)s)
    ''', dbconn, params={'shape_id': shape_id, 'start_time': start_time, 'end_time': end_time})

  return trips_to_match['scheduled_trip_id']

start_time, end_time = '2017-11-27 06:30:00', '2017-11-27 07:30:00'

shapes = ['660',]
nshapes = len(shapes)
for i, shape_id in enumerate(shapes):
  print("{} / {} shapes".format(i+1, nshapes))
  trips_to_match = get_trips(shape_id, start_time, end_time)
  ntrips = len(trips_to_match)
  
  
  for j, trip in enumerate(trips_to_match):
    print(" {} / {} trips".format(j+1, ntrips))
    match_gps(trip, start_time, end_time)

