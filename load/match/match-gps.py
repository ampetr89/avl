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
def setup_time(start_time, end_time):
  cur.execute('''
    drop table if exists etl.bus_position__time
    ''')

  cur.execute('''
  create table etl.bus_position__time
  as 
  select *
   from bus_position
   where datetime between %(start_time)s and %(end_time)s
  ''', {'start_time': start_time, 'end_time': end_time}
    )

  cur.execute('create index idx_bus_position__time on etl.bus_position__time(scheduled_trip_id)')
  pg.commit()


def get_shapes():
  shapes = pd.read_sql('''
    select a.shape_id,
      ST_length(c.the_geom::geography)/1000 as shape_length, -- length in km
      count(*) as ntrips -- number of trips that use this shape
    from 
      (select shape_id, a.scheduled_trip_id
       /* look up the shape_id of the trips in the api data, 
       and grab the shapes that we havent matched yet*/
       from 
          (select scheduled_trip_id
           from etl.bus_position__time
           group by 1) as a
          join gtfs.trips as b
           on a.scheduled_trip_id = b.scheduled_trip_id
          ) as a
      left join(
       select shape_id
          from gtfs.matched_shape
          group by 1
        ) as b
       on a.shape_id = b.shape_id
      join gtfs.shape_line as c
       on a.shape_id = c.shape_id
       where b.shape_id is not null
       group by 1,2
       order by 3 desc
       limit 1
    ''', dbconn) # params={'start_time': start_time, 'end_time': end_time}

  return shapes[['shape_id', 'shape_length']]

def setup_shape(shape_id):
  cur.execute('''
    drop table if exists etl.matched_ways__shape
    ''')
  cur.execute('''
    create table etl.matched_ways__shape
     as select * from gtfs.matched_ways
     where shape_id = %(shape_id)s
    ''', {'shape_id': shape_id})

  cur.execute('''
    create index gdx_matched_ways__shape on etl.matched_ways__shape using gist(the_geom)
    ''')  

  pg.commit()

def get_routes(shape_id):
  routes = pd.read_sql('''
    select route_id
    from gtfs.trips
    where shape_id = %(shape_id)s
    group by 1
    ''', dbconn, params={'shape_id': shape_id})

  return routes['route_id']


def setup_route(route_id):
  cur.execute('''
    drop table if exists etl.bus_position_match__route
    ''')
  cur.execute('''
    create table etl.bus_position_match__route
     as select *
     from bus_position_match
     limit 0
    ''', {'shape_id': shape_id})

  cur.execute('''
    create index gdx_bus_position_match__route 
      on etl.bus_position_match__route (route_id, trip_dist_pct)
    ''')

  pg.commit()

def get_trips(route_id, start_time, end_time):
  """
  get the trips for the particular shape, only the ones that occured
  during the interval we care about and who have not already been matched
  """
  trips_to_match = pd.read_sql('''
   select scheduled_trip_id
    from gtfs.trips
     where route_id = %(route_id)s
      and scheduled_trip_id in (
          select scheduled_trip_id from etl.bus_position__time
          group by 1)
      and scheduled_trip_id not in (
          select scheduled_trip_id from bus_position_match 
         where datetime between %(start_time)s and %(end_time)s group by 1)
      group by 1
    ''', 
    dbconn, 
    params={'route_id': route_id, 'start_time': start_time, 'end_time': end_time})

  return trips_to_match['scheduled_trip_id']

def match_gps(scheduled_trip_id, route_id, shape_length):
  cur.execute('''
  drop table if exists etl.bus_position__trip
  ''')

  cur.execute('''
  create table etl.bus_position__trip -- contains just this particular trip
  as 
  select * 
   from etl.bus_position__time
   where scheduled_trip_id = %(scheduled_trip_id)s
  ''', {'scheduled_trip_id': scheduled_trip_id}
    )

  cur.execute('''
  create index gidx_bus_position__trip on etl.bus_position__trip using gist (the_geom) 
    ''')
  pg.commit()

  assert False, "stopping here"
  cur.execute('''
   insert into etl.bus_position_match__route
     select *,
        0::int as interp, 
        %(route_id)d as route_id, 
        sum(length) over (partition by scheduled_trip_id, vehicle_id)/%(shape_length)d,
        NULL::decimal as headway -- updated later
      from 
      (select a.*,
       row_number() over
         (partition by scheduled_trip_id, vehicle_id, datetime order by dist_meters asc) as dist_rank
      
        from 
         (select t.*, 
            s.way_id, s.begin_heading, s.end_heading, s.weighted_grade, 
            s.speed as speed_limit, s.road_class, s.length,
            s.shape_id, s.edge_seq_num, 
            ceiling(ST_distance(t.the_geom::geography, s.the_geom::geography)) as dist_meters

          from etl.bus_position__trip as t
          join geog_conversion as g
           on 1=1
          left join etl.matched_ways__shape as s
           on ST_Dwithin(t.the_geom, s.the_geom, 50*g.mrad)
          ) as a
      ) as b
      where dist_rank = 1
  ''', {'route_id': route_id, 'shape_length': shape_length})
  pg.commit()



setup_time(start_time, end_time)

shapes = get_shapes()
nshapes = len(shapes)
print('found {} shapes to match'.format(nshapes))

for i, row in shapes.iterrows():
  print("{} / {} shapes".format(i+1, nshapes))
  shape_id = row['shape_id']
  shape_length = row['shape_length']
  print(shape_id, shape_length)
  setup_shape(shape_id)
  
  routes = get_routes(shape_id)
  nroutes = len(routes)

  for j, route_id in enumerate(routes):
    print(" {} / {} routes".format(j+1, nroutes))
    setup_route(route_id)
    trips_to_match = get_trips(route_id, start_time, end_time)
    print(trips_to_match[0])
    ntrips = len(trips_to_match)

    for k, trip_id in enumerate(trips_to_match):
      print(" {} / {} trips".format(k+1, ntrips))
      match_gps(trip_id, route_id, shape_length)

  # calculate headways
  insert_route()