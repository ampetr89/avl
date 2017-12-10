import pandas as pd
import json

#%%
import sys
sys.path.append('../')
from db import Db

db = Db()
dbconn = db.conn
pg = db.pg
cur = pg.cursor()

"""
cur.execute('''
/*select st_asgeojson(the_geom) as the_geom
from(*/
 select the_geom from gtfs.matched_ways group by 1 limit 30000
/*) a*/
	''')
"""

cur.execute('''
SELECT row_to_json(featcoll)
   FROM 
    (SELECT 'FeatureCollection' As type, array_to_json(array_agg(feat)) As features
     FROM (SELECT 'Feature' As type,
        ST_AsGeoJSON(tbl.the_geom)::json As geometry,
        row_to_json((SELECT l FROM (SELECT way_id, names, road_class) As l)
  ) As properties
  FROM (select the_geom, way_id, names, road_class from gtfs.matched_ways group by 1,2,3,4 limit 28500) As tbL   
 )  As feat 
)  As featcoll;
''')

f = open('bus-layer.json', 'w')
f.write(json.dumps(cur.fetchall()[0][0]))
f.close()
