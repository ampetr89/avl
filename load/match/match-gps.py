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

start_time, end_time = '2017-11-30 06:00:00', '2017-11-30 11:00:00'


#%%
def setup(shape_id, start_time, end_time):
  cur.execute('''
    drop table if exists bus_position_temp
    ''')

  cur.execute('''
  create table bus_position_temp
  as 
  select *
   from bus_position
   where datetime between %(start_time)s and %(end_time)s
  ''', {'start_time': start_time, 'end_time': end_time}
    )

  cur.execute('create index idx_bus_position_temp on bus_position_temp(scheduled_trip_id)')
  pg.commit()


def get_shapes(start_time, end_time):
  shapes = pd.read_sql('''
    select a.shape_id, count(*) as ntrips from 
      (select shape_id, a.scheduled_trip_id
       from 
          (select scheduled_trip_id
          from bus_position_temp 
          group by 1) as a
          join gtfs.trips as b
           on a.scheduled_trip_id = b.scheduled_trip_id
          ) as a
      join(
       select shape_id
          from gtfs.matched_shape
          group by 1
      ) as b
       on a.shape_id = b.shape_id
       where b.shape_id is not null
       group by 1
       order by 2 desc
       limit 1
    ''', dbconn, params={'start_time': start_time, 'end_time': end_time})

  return shapes['shape_id']

def setup_match_way(shape_id)
  cur.execute('''
    drop table if exists gtfs.matched_ways_temp
    ''')
  cur.execute('''
    create table gtfs.matched_ways_temp
     as select * from gtfs.matched_ways
     where shape_id = %(shape_id)s
    ''', {'shape_id': shape_id})

  cur.execute('''
    create index gdx_matched_ways_temp on gtfs.matched_ways_temp using gist(the_geom)
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
          select scheduled_trip_id from bus_position_temp 
          group by 1)
      and scheduled_trip_id not in (
          select scheduled_trip_id from bus_position_match 
         where datetime between %(start_time)s and %(end_time)s group by 1)
      group by 1
    ''', 
    dbconn, 
    params={'shape_id': shape_id, 'start_time': start_time, 'end_time': end_time})

  return trips_to_match['scheduled_trip_id']

def match_gps(scheduled_trip_id):
  cur.execute('''
  drop table if exists bus_position_temp_trip
  ''')

  cur.execute('''
  create table bus_position_temp_trip -- contains just this particular trip
  as 
  select * 
   from bus_position_temp -- contains just the trips with this shape
   where scheduled_trip_id = %(scheduled_trip_id)s
  ''', {'scheduled_trip_id': scheduled_trip_id}
    )

  cur.execute('''
  create index gidx_bus_position_temp on bus_position_temp_trip using gist (the_geom) 
    ''')
  pg.commit()

  cur.execute('''
    drop table if exists bus_position_match_temp;
    ''')
  cur.execute('''
  /* insert into bus_position_match(datetime, scheduled_trip_id, route_short_name, direction_text,
                                trip_headsign, gps_lon, gps_lat, deviation ,vehicle_id,
                                 way_id, begin_heading, end_heading, weighted_grade, speed_limit, road_class, length,
                                shape_id, edge_seq_num, /*edge_geom,*/ dist_rank) */
  create table bus_position_match_temp AS
   select *, 0::int as interp from 
  (select datetime, scheduled_trip_id, 
    route_short_name, direction_text, trip_headsign,
    lon as gps_lon, lat as gps_lat, deviation, vehicle_id, 
    way_id, begin_heading, end_heading, weighted_grade, speed_limit, road_class, length,
    shape_id, edge_seq_num,

   /* edge_geom as the_geom, -- writing geometry can slow things down */
    row_number() over (partition by scheduled_trip_id, datetime order by dist_meters asc) as dist_rank
  from 
  (
   select a.*, 
          c.way_id, c.begin_heading, c.end_heading, c.weighted_grade, c.speed as speed_limit, c.road_class, c.length,
          b.shape_id, edge_seq_num, /*c.the_geom as edge_geom,*/
          ceiling(ST_distance(a.the_geom::geography, c.the_geom::geography)) as dist_meters

      from bus_position_temp_trip as a  
      join gtfs.trips as b
       on a.scheduled_trip_id = b.scheduled_trip_id 
      join geog_conversion as g
       on 1=1
      left join gtfs.matched_ways_temp as c
       on b.shape_id = c.shape_id
       and ST_Dwithin(a.the_geom, c.the_geom, 50*g.mrad)
  ) as a ) as b
  where dist_rank = 1
  ''')
  pg.commit()



setup(start_time, end_time)

shapes= get_shapes(start_time, end_time)
nshapes = len(shapes)
print('found {} shapes to match'.format(nshapes))
print(shapes)
trips_to_match = get_trips(shapes[0], start_time, end_time)
print(trips_to_match)

for i, shape_id in enumerate(shapes):
  print("{} / {} shapes".format(i+1, nshapes))
  setup_match_way(shape_id)
  break
  trips_to_match = get_trips(shape_id, start_time, end_time)
  ntrips = len(trips_to_match)
  
  
  for j, trip in enumerate(trips_to_match):
    print(" {} / {} trips".format(j+1, ntrips))
    match_gps(trip)
