import requests
import json
import pandas as pd

import sys
sys.path.append('../')
from db import Db
import polyline
from io import StringIO

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


start_time, end_time = '2017-11-27 06:30:00', '2017-11-27 07:30:00'

shapes_to_get = pd.read_sql("""
    select shape_id, ST_asgeojson(the_geom) as geojson
    from gtfs.shape_line
    where shape_id in (
        select shape_id
            from
            (select scheduled_trip_id, count(*) as ngps
            from bus_position
            where datetime between %(start_time)s and %(end_time)s
            group by 1
            ) as a
            join gtfs.trips as b
             on a.scheduled_trip_id = b.scheduled_trip_id
        )
      and shape_id not in (select distinct shape_id from gtfs.matched_shape)
    """, dbconn, params={'start_time': start_time, 'end_time': end_time})
print('pulled {} shapes'.format(len(shapes_to_get)))
#print(shapes_to_get.head())



cur.execute('truncate table etl.matched_ways');
pg.commit()

from_local = False 

def pg_to_sql(df, table, schema="gtfs"):
    # print('loading {} rows to {}'.format(len(df), table))
    f = StringIO(df.to_csv(sep=",", index=False, header=False))

    columns = ','.join(df.columns)
    copy_statement = "COPY {}.{} ({}) FROM STDIN CSV;".format(schema, table, columns)
    
    cur.copy_expert(copy_statement, f)
    pg.commit()

def update_way_geom(shape_id):
    cur.execute("""
        alter table etl.matched_ways
        add column start_lon float,
        add column start_lat float,
        add column end_lon float,
        add column end_lat float
        """)

    cur.execute("""
        update etl.matched_ways as a
        set start_lon = b.lon, start_lat = b.lat
        from gtfs.matched_shape as b
         where b.shape_id = '{}'
         and a.begin_shape_index = b.shape_seq_num
        """.format(shape_id))
    cur.execute("""
        update etl.matched_ways as a
        set end_lon = b.lon, end_lat = b.lat
        from gtfs.matched_shape as b
         where b.shape_id = '{}'
         and a.end_shape_index = b.shape_seq_num
        """.format(shape_id))

    cur.execute("""
        update etl.matched_ways set the_geom = 
        ST_SETSRID(ST_MAKELINE(ST_makepoint(start_lon, start_lat), ST_makepoint(end_lon, end_lat)), 4326)
        """)

    cur.execute("""
        alter table etl.matched_ways
        drop column start_lon,
        drop column start_lat,
        drop column end_lon,
        drop column end_lat
        """)

    cur.execute("""
        insert into gtfs.matched_ways
        select * from etl.matched_ways
        """)
    pg.commit()

nshapes = len(shapes_to_get)
for i in range(nshapes):
    
    record = shapes_to_get.iloc[i]
    shape_id = record['shape_id']
    print('{}: {} / {}'.format(shape_id, i+1, nshapes))
    coords = json.loads(record['geojson'])['coordinates']

    # print('{} total coordinates'.format(len(coords)))
    
    coord_list = [ {'lon': coord[0], 'lat': coord[1]} for coord in coords]
    
    url_args.update({'shape': coord_list})
    if from_local:
        with open('results/shape_{}.json'.format(shape_id), 'r') as f:
            response = json.loads(f.read())
    
    else:
        r = requests.get(url , data=json.dumps(url_args))
        with open('results/shape_{}.json'.format(shape_id), 'w') as f:
            f.write(r.text)
        response = json.loads(r.text)

    
    if 'matched_points' in response:
        matched_points = pd.DataFrame(response['matched_points'])
        matched_points['shape_pt_sequence'] = range(1, len(matched_points)+1)
    else:
        print('warning: matched_points field not provided in response')    
    
    matched_ways = pd.DataFrame(response['edges'])
    if 'names' in matched_ways:
        matched_ways['names'] = matched_ways['names'].apply(lambda x: ' / '.join(x) if type(x)==list else x)
    else:
        matched_ways['names'] = ''
    matched_ways['shape_id'] = shape_id
    matched_ways['edge_seq_num'] = range(1, len(matched_ways)+1)

    
    matched_shape = polyline.decode(response['shape'])
    matched_shape = [ {'lat': latlon[0]/10, 'lon': latlon[1]/10} for latlon in matched_shape]
    matched_shape = pd.DataFrame(matched_shape)
    matched_shape['shape_id'] = shape_id
    matched_shape['shape_seq_num'] = range(0, len(matched_shape)) ## this one has to start at 0 so that it matches the mapzen "begin/end_shape_index"
    
    #print('loading results')
    
    #https://wiki.postgresql.org/wiki/Psycopg2_Tutorial

    if 'matched_points' in response:
        pg_to_sql(matched_points,'matched_point')
    pg_to_sql(matched_shape,'matched_shape')
    pg_to_sql(matched_ways,'matched_ways', schema="etl")
    update_way_geom(shape_id)

    
#https://api.mapbox.com/mapbox/driving/-117.1728265285492,32.71204416018209;-117.17288821935652,32.712258556224;-117.17293113470076,32.712443613445814;-117.17292040586472,32.71256999376694;-117.17298477888109,32.712603845608285;-117.17314302921294,32.71259933203019;-117.17334151268004,32.71254065549407?access_token={}
#https://api.mapbox.com/matching/v5/mapbox/driving/-117.1728265285492,32.71204416018209;-117.17288821935652,32.712258556224;-117.17293113470076,32.712443613445814;-117.17292040586472,32.71256999376694;-117.17298477888109,32.712603845608285;-117.17314302921294,32.71259933203019;-117.17334151268004,32.71254065549407?access_token
print('Done')