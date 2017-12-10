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



cur.execute('''
SELECT row_to_json(featcoll)
   FROM 
    (SELECT 'FeatureCollection' As type, array_to_json(array_agg(feat)) As features
     FROM (SELECT 'Feature' As type,
        ST_AsGeoJSON(tbl.the_geom)::json As geometry,
        row_to_json((SELECT l FROM (SELECT way_id, name, type, z_order) As l)
  ) As properties
  FROM (select the_geom, way_id, name, type, z_order 
        from public.bus_layer 
        group by 1,2,3,4,5
        order by ST_Distance(the_geom, st_setsrid(ST_makepoint(-77.036432, 38.907279), 4326)) asc
         limit 9000) As tbL   
 )  As feat 
)  As featcoll;
''')

f = open('bus_layer.json', 'w')
f.write(json.dumps(cur.fetchall()[0][0]))
f.close()
