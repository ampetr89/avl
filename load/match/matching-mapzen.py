import requests
import json
import pandas as pd

import sys
sys.path.append('../')
from db import Db
import polyline
from io import StringIO
import os 

db = Db()
dbconn = db.conn
pg = db.pg
cur = pg.cursor()


#%%

apikey = "mapzen-xEfx4F5"
url = 'https://valhalla.mapzen.com/trace_attributes?api_key={}'.format(apikey)


url_args = {
    "costing":"auto",
      "shape_match":"walk_or_snap",
      "filters":{"action":"include",
          "attributes":[
              "shape",
              "edge.names","edge.id", "edge.way_id", 
              "edge.weighted_grade","edge.speed", "edge.length",
              "edge.road_class", "edge.begin_heading", "edge.end_heading",
            "edge.begin_shape_index", "edge.end_shape_index",
            "matched.edge_index",
              "matched.distance_along_edge","matched.point", "matched.distance_from_trace_point",
              "matched.type"]},
      "shape": []
}


start_time, end_time = '2017-11-30 06:30:00', '2017-11-30 10:30:00'

shapes_to_get = pd.read_sql("""
    select A.shape_id, ST_asgeojson(the_geom) as geojson, ngps, ntrips
    from gtfs.shape_stops_removed_line as A
    join (
        select shape_id, count(distinct a.scheduled_trip_id) as ntrips, sum(ngps) as ngps
            from
            (select scheduled_trip_id, count(*) as ngps
            from bus_position
            where datetime between %(start_time)s and %(end_time)s
            group by 1
            ) as a
            join gtfs.trips as b
             on a.scheduled_trip_id = b.scheduled_trip_id
         group by 1
        ) as B
       on A.shape_id = B.shape_id
      where A.shape_id not in (select distinct shape_id from gtfs.matched_shape)
      order by ntrips desc, ngps desc
      limit 25
    """, dbconn, params={'start_time': start_time, 'end_time': end_time})
print('pulled {} shapes'.format(len(shapes_to_get)))
#print(shapes_to_get.head())


# from_local = False 

def pg_to_sql(df, table, schema="gtfs"):
    # https://wiki.postgresql.org/wiki/Psycopg2_Tutorial
    # print('loading {} rows to {}'.format(len(df), table))
    f = StringIO(df.to_csv(sep=",", index=False, header=False))

    columns = ','.join(df.columns)
    copy_statement = "COPY {}.{} ({}) FROM STDIN CSV;".format(schema, table, columns)
    
    cur.copy_expert(copy_statement, f)
    pg.commit()

def insert_matched_ways():
    cur.execute("""
        insert into etl.matched_ways_geom
        select a1.shape_id, edge_seq_num,
           ST_SetSRID(ST_MakeLine(ST_MakePoint(lon, lat) order by shape_seq_num), 4326) as the_geom
         from etl.matched_ways as a1
         join gtfs.matched_shape as b1
          on a1.shape_id = b1.shape_id
         and b1.shape_seq_num between a1.begin_shape_index and a1.end_shape_index
         group by 1,2
        """)

    cur.execute("""
        insert into gtfs.matched_ways
            select a.*, b.the_geom
            from etl.matched_ways as a
            join etl.matched_ways_geom as b
              on a.shape_id = b.shape_id
             and a.edge_seq_num = b.edge_seq_num
        """)
    pg.commit()


nlocal = 0
napi = 0
nshapes = len(shapes_to_get)
for i, record in shapes_to_get.iterrows():
    cur.execute('truncate table etl.matched_ways');
    cur.execute('truncate table etl.matched_ways_geom');
    pg.commit()
    
    #record = shapes_to_get.iloc[i]
    shape_id = record['shape_id']
    print('{}: {} / {}'.format(shape_id, i+1, nshapes))
    coords = json.loads(record['geojson'])['coordinates']

    # print('{} total coordinates'.format(len(coords)))
    
    coord_list = [ {'lon': coord[0], 'lat': coord[1]} for coord in coords]
    
    url_args.update({'shape': coord_list})
    
    result_file_name = 'results/shape_{}.json'.format(shape_id)
    from_local = os.path.isfile(result_file_name)
    
    if from_local:
        nlocal += 1
        with open(result_file_name, 'r') as f:
            response = json.loads(f.read())
    
    else:
        napi += 1
        # save all api results to a file
        r = requests.get(url , data=json.dumps(url_args))
        with open(result_file_name, 'w') as f:
            f.write(r.text)
        response = json.loads(r.text)

    
    if 'matched_points' in response:
        matched_points = pd.DataFrame(response['matched_points'])
        matched_points['shape_pt_sequence'] = range(0, len(matched_points))
    else:
        print('warning: matched_points field not provided in response')    
    
    if 'edges' not in response:
        print('warning: edges field not provided in response. skipping this shape')
        continue

    matched_ways = pd.DataFrame(response['edges'])
    if 'names' in matched_ways:
        matched_ways['names'] = matched_ways['names'].apply(lambda x: ' / '.join(x) if type(x)==list else x)
    else:
        matched_ways['names'] = ''

    matched_ways['shape_id'] = shape_id
    matched_ways['edge_seq_num'] = range(0, len(matched_ways))

    
    matched_shape = polyline.decode(response['shape'])
    matched_shape = [ {'lat': latlon[0]/10, 'lon': latlon[1]/10} for latlon in matched_shape]
    matched_shape = pd.DataFrame(matched_shape)
    matched_shape['shape_id'] = shape_id
    matched_shape['shape_seq_num'] = range(0, len(matched_shape)) ## this one has to start at 0 so that it matches the mapzen "begin/end_shape_index"
    
    

    if 'matched_points' in response:
        # matched_point table is not that useful
        # just shows mapping between points you gave it and matched points
        pg_to_sql(matched_points,'matched_point')

    pg_to_sql(matched_shape,'matched_shape')
    pg_to_sql(matched_ways,'matched_ways', schema="etl")

    insert_matched_ways()


print('Done. Used {} api calls and read {} from local file'.format(napi, nlocal))