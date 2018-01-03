import pandas as pd

#%%
import sys
sys.path.append('../')
from db import Db

'''
connect to the database
'''
db = Db()
dbconn = db.conn
pg = db.pg
cur = pg.cursor()


#%%
'''
match the API data for a certain time period
'''
start_time, end_time = '2017-12-13 00:00:00', '2017-12-13 23:59:59'


#%%
def setup_time(start_time, end_time):
  '''
  we are going to be hitting the bus_position table a lot, so lets make a
  table with just the time range we need 
  '''
  cur.execute('''
    drop table if exists etl.bus_position__time
    ''')

  cur.execute('''
  create table etl.bus_position__time
  as 
  select *  /* , route_id */
   from bus_position as a
   /*join (select scheduled_trip_id, route_id
    from gtfs.trips
    group by 1,2) as b
  on a.scheduled_trip_id = b.scheduled_trip_id */
   where datetime between %(start_time)s and %(end_time)s
  ''', {'start_time': start_time, 'end_time': end_time}
    )

  cur.execute('create index idx_bus_position__time on etl.bus_position__time(scheduled_trip_id)')
  pg.commit()



def get_shapes(start_time, end_time):
  '''
  look up the shape_id of the trips in the api data, 
   and grab the shapes that we havent matched yet
  '''

  shapes = pd.read_sql('''
    select S1.shape_id, ST_length(S2.the_geom::geography)/1000 as shape_length, n_runs
    from
    (
    select shape_id, sum(n_runs) as n_runs  from 
    (
    select scheduled_trip_id, count(*) as  n_runs
    from
    (select run_id, scheduled_trip_id
    from etl.bus_position__time
     group by 1,2) as a
    left join
    ( select run_id
     from bus_position_match
     where datetime between %(start_time)s and %(end_time)s
     group by 1) as b
    on a.run_id = b.run_id
    where b.run_id is null
    group by 1
    ) as R
    join gtfs.trips as T
     on R.scheduled_trip_id = T.scheduled_trip_id
    group by 1
    ) as S1
    join gtfs.shape_line as S2
     on S1.shape_id = S2.shape_id
    order by n_runs desc
   ''', dbconn, params= {'start_time': start_time, 'end_time': end_time})

  """
  shapes = pd.read_sql('''
    select a.shape_id,
      ST_length(c.the_geom::geography)/1000 as shape_length, -- length in km
      count(*) as ntrips -- number of trips that use this shape
    from 
      (select shape_id, a.scheduled_trip_id
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
    ''', dbconn) 
  """
  return shapes[['shape_id', 'shape_length']]

def setup_shape(shape_id):
  '''
  we are going to be hitting the gtfs.matched_ways a lot, so lets make a
  table with just the shape we need 
  '''
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
  '''
  grab all the routes that use this shape
  '''
  routes = pd.read_sql('''
    select route_id
    from gtfs.trips
    where shape_id = %(shape_id)s
    group by 1
    ''', dbconn, params={'shape_id': shape_id})

  return routes['route_id']


def setup_route(route_id):
  '''
  we'll process all the trips for a particular route, and once we
  have them we'll move them in batch to the final table. The
  reason is to eventually include a calculation of headway (seconds
  or distance between vehicles on the same route), and this would
  be an easy place to put that calculation.
  '''
  cur.execute('''
    truncate table etl.bus_position_match__route
    ''')

  pg.commit()

def get_runs(route_id):
  '''
  get the runs for the particular shape, only the ones that occured
  during the interval we care about and who have not already been matched
  '''
  runs_to_match = pd.read_sql('''
   select run_id
   from etl.bus_position__time
   where scheduled_trip_id in (select scheduled_trip_id from gtfs.trips where route_id = %(route_id)s)
    and run_id not in (select run_id from bus_position_match group by 1)
   group by 1
    ''', 
    dbconn, 
    params={'route_id': route_id})

  return runs_to_match['run_id']

def match_gps(run_id):
  '''
  match a run! look at the matched_ways__shape which has already 
  determined which OSM ways are used for this route. all that
  is needed is to find the closest way from that subset
  for each gps point
  '''
  cur.execute('''
  drop table if exists etl.bus_position__run
  ''')

  cur.execute('''
  create table etl.bus_position__run -- contains just this particular run
  as 
  select * 
   from etl.bus_position__time
   where run_id = %(run_id)s
  ''', {'run_id': run_id}
    )

  cur.execute('''
  create index gidx_bus_position__run on etl.bus_position__run using gist (the_geom) 
    ''')
  pg.commit()


  cur.execute('''
  drop table if exists etl.bus_position_match__run
  ''')

  '''
  assemble the matched run in two steps.
  1. match each gps point to the closest edge segment
  '''
  cur.execute('''
    create table etl.bus_position_match__run
    AS
    select *
      from 
      (select a.*,
       row_number() over
         (partition by run_id, datetime order by dist_meters asc) as dist_rank,
         0::int as interp
       
        from 
         (select t.run_id, t.datetime, t.deviation, 
            s.way_id, s.begin_heading, s.end_heading, s.weighted_grade, 
            s.speed, s.road_class, s.length,
            s.shape_id, s.edge_seq_num, 
            ceiling(ST_distance(t.the_geom::geography, s.the_geom::geography)) as dist_meters

          from etl.bus_position__run as t
          join geog_conversion as g
           on 1=1
          left join etl.matched_ways__shape as s
           on ST_Dwithin(t.the_geom, s.the_geom, 50*g.mrad)
          ) as a
      ) as b
      where dist_rank = 1

    ''')


  '''
  2. make the matching contiguous: if there are any gaps, fill
  them in bus flag as interpolated
  '''
  cur.execute('''
   insert into etl.bus_position_match__run(
    run_id, datetime, deviation, 
    way_id , begin_heading, end_heading, weighted_grade, speed, road_class, length,
    shape_id, edge_seq_num,    
    dist_meters, interp
    )

    select 
      run_id, datetime, deviation, 
      a.way_id , a.begin_heading, a.end_heading, a.weighted_grade, a.speed, a.road_class, a.length,
      a.shape_id, a.edge_seq_num, 
      NULL::float as dist_meters, 1::int as interp

      from etl.matched_ways__shape as a
      join 
        (select *, lead(edge_seq_num) over (order by datetime) as next_edge_seq_num
         from etl.bus_position_match__run
        )as b
       on a.edge_seq_num > b.edge_seq_num
       and a.edge_seq_num < b.next_edge_seq_num
  ''')

  '''
  finally, move the run into the route table
  '''
  cur.execute('''
    insert into etl.bus_position_match__route(run_id, datetime, deviation,
     way_id, begin_heading, end_heading, weighted_grade,
     speed, road_class, length, 
     shape_id, edge_seq_num,
     dist_meters, interp)

    select run_id, datetime, deviation,
      way_id, begin_heading, end_heading, weighted_grade,
      speed, road_class, length,
      shape_id, edge_seq_num,
      dist_meters,  interp
    from etl.bus_position_match__run
    ''')
  
  pg.commit()


def insert_route(route_id, shape_length):
  '''
  after all runs for this route are matched, 
  move them in bulk to the main table
  '''
  cur.execute('''
    insert into bus_position_match
    (run_id, datetime, deviation, 
    way_id, begin_heading, end_heading, weighted_grade, speed, road_class, length,
    shape_id, edge_seq_num, dist_meters,
    interp, route_id, trip_dist_pct)
    
    select 
     run_id, datetime, deviation, 
     way_id, begin_heading, end_heading, weighted_grade, speed, road_class, length,
     shape_id, edge_seq_num, dist_meters,
     0::int as interp, %(route_id)s, 
     (sum(length) over (partition by run_id order by datetime))/%(shape_length)s trip_dist_pct

     from etl.bus_position_match__route
    ''', {'route_id': route_id, 'shape_length': shape_length})

  pg.commit()

setup_time(start_time, end_time)

shapes = get_shapes(start_time, end_time)
nshapes = len(shapes)
print('found {} shapes to match'.format(nshapes))

for i, row in shapes.iterrows():
  print("{} / {} shapes".format(i+1, nshapes))
  shape_id = row['shape_id']
  shape_length = row['shape_length']
  print('shape', shape_id, shape_length)

  setup_shape(shape_id)
  
  routes = get_routes(shape_id)
  nroutes = len(routes)

  for j, route_id in enumerate(routes):
    print(" {} / {} routes".format(j+1, nroutes))
    print('route_id', route_id)
    setup_route(route_id)
    runs_to_match = get_runs(route_id)
    #print(trips_to_match[0])
    
    nruns = len(runs_to_match)
    print('  {} runs'.format(nruns))

    for k, run_id in enumerate(runs_to_match):
      #print(" {} / {} runs".format(k+1, nruns))
      #print('run_id', run_id)
      match_gps(run_id)


  # calculate headways...
  insert_route(route_id, shape_length)
  