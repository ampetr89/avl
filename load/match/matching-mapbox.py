import requests
import json
import pandas as pd

import os
import polyline

import sys
sys.path.append('../')
from db import Db

dbconn = Db().conn

access_token = "pk.eyJ1IjoiYW5uYW1wZXRyb25lIiwiYSI6ImU0NzFkZmI3M2EyYThlNjc4MGI0ZWVjOGVjNDU2OTNkIn0.3uRcGR7rnA1xvW7j-aWFtQ"
endpoint = "matching/v5"
profile = "mapbox/driving"
#coords = "-117.1728265285492,32.71204416018209;-117.17288821935652,32.712258556224;-117.17293113470076,32.712443613445814;-117.17292040586472,32.71256999376694;-117.17298477888109,32.712603845608285;-117.17314302921294,32.71259933203019;-117.17334151268004,32.71254065549407"
url = "https://api.mapbox.com/{endpoint}/{profile}/{coords}?{paramstr}"


params = {
    'access_token': access_token,
    'tidy': 'false',
    'geometries': 'geojson',
    'overview': 'full',
    'steps': 'true'
}
paramstr = '&'.join([ '='.join(par) for par in params.items()])


url_args = {
    'profile': profile,
    'endpoint': endpoint,
    'coords': "",
    'paramstr': paramstr
}


shapes = pd.read_sql("""
    select shape_id, ST_asgeojson(the_geom_simple) as geojson
    from gtfs.shape_stops_removed_line
    where shape_id = '2478'
    """, dbconn)
print('pulled {} shapes'.format(len(shapes)))
print(shapes.head())


def make_geosjson(coords):
	return  '\
		{\
		  "type": "Feature",\
		  "geometry": {\
		    "type": "LineString",\
		    "coordinates": '+json.dumps(coords['coordinates'])+'\
		  },\
		  "properties": {"hello": "world" }\
		}'
N = 90 # mapbox only lets you do 100 at a time
for i, record in shapes.iterrows():
    # record = shapes.iloc[i]
    shape_id = record['shape_id']
    coords = json.loads(record['geojson'])['coordinates']
    result_file_name = 'results/mapbox/shape_{}.json'.format(shape_id)
    #print(geojson['coordinates'][0:4])
    n = len(coords)
    print('{} total coordinates'.format(n))
    m = 0
    prev_coord = []
    while m < n:
        to = min(m+N, n)

        send_coords = prev_coord + coords[m:to]

        
        print('m={}, to={}, len(coords)={}, len(send_coords)={}'.format(m, to, len(coords), len(send_coords)))
        # print(send_coords[0:2])
        # print(send_coords[-1])

        coord_str = ';'.join([','.join([str(a) for a in latlon]) for latlon in send_coords])
        url_args.update({'coords': coord_str})
        r = requests.get(url.format(**url_args))
        #print(r.url)
        m += N
        prev_coord = [send_coords[-1]]
        
        from_local = os.path.isfile(result_file_name)
        if from_local:
            print('reading from file')
            with open(result_file_name, 'r') as f:
                response = json.loads(f.read())
        else:
            r = requests.get(url.format(**url_args))
            # print(r.url)
            with open(result_file_name, 'w') as f:
                f.write(r.text)
            response = json.loads(r.text)
        #print(response['matchings'][0]['geometry'])
        #print(len(response['matchings'][0]))
        matchings = response['matchings']
        #print(len(matchings))
        legs = [leg for leg in matchings[0]['legs']]
        #print(len(legs))
        steps = [leg['steps'] for leg in legs]
        #print([len(step) for step in steps])
        #print(len(steps))
        results_flat = [s for step in steps for s in step]
        print(results_flat[0].keys())
        results_df = pd.DataFrame(results_flat)
        results_df['geometry'] = results_df['geometry'].apply(make_geosjson)
        print(results_df.head())
        results_df.to_csv(result_file_name.replace('.json', '.csv'), index=False)
        #geoms = [{ 'step_id':i, 'coord_seq': j, 'lat': coord[0],'lon': coord[1]} for i, res in enumerate(results_flat) for j, coord in enumerate(polyline.decode(res['geometry']))]
        #geoms = [{ 'step_id':i, 'coord_seq': j, 'geojson': res['ge']} for i, res in enumerate(results_flat) for j, coord in enumerate(polyline.decode(res['geometry']))]
        #geoms = pd.DataFrame(geoms)

        #geoms.to_csv(result_file_name.replace('.json', '.csv'), index=False)
        break

#https://api.mapbox.com/mapbox/driving/-117.1728265285492,32.71204416018209;-117.17288821935652,32.712258556224;-117.17293113470076,32.712443613445814;-117.17292040586472,32.71256999376694;-117.17298477888109,32.712603845608285;-117.17314302921294,32.71259933203019;-117.17334151268004,32.71254065549407?access_token={}
#https://api.mapbox.com/matching/v5/mapbox/driving/-117.1728265285492,32.71204416018209;-117.17288821935652,32.712258556224;-117.17293113470076,32.712443613445814;-117.17292040586472,32.71256999376694;-117.17298477888109,32.712603845608285;-117.17314302921294,32.71259933203019;-117.17334151268004,32.71254065549407?access_token

