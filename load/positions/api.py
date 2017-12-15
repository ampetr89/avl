import requests
import json
from db import Db # handles the sqlalchemy as psycopg2 imports
import pandas as pd
from pandas.io import sql # optional: for executing additonal SQL
from time import sleep
from datetime import  datetime as dt
from datetime import timedelta
import logging
import os
from io import StringIO
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-M', '--minutes', 
    type=int,
    help='How long to run the program (in minutes)', 
    default=60)
parser.add_argument('-i', '--interval', 
    type=int,
    help='Interval between sucecssive API calls (in seconds)', 
    default=5)

args = parser.parse_args()
run_minutes = args.minutes
interval_seconds = args.interval

wd = os.getcwd()
logfile = os.path.join(wd, 'api.log')

logging.basicConfig(format="%(asctime)s - %(message)s", filename=logfile, 
    level=logging.DEBUG)


#%%
# make a database connection
db = Db()
dbconn = db.conn
pg = db.pg
cur = pg.cursor()

logging.info("Database connection made")

#%%
headers = {
    # Request headers
    'api_key': '14748bd7797040e680442161663ca61d',
}

params = { # official API parameters
    # Request parameters
    #'RouteID': 'B30',
    #'Lat': '{number}',
    #'Lon': '{number}',
    #'Radius': '{number}',
}


def initial():
    df = pd.read_sql('''
    select * from 
        (select *, row_number() over (partition by scheduled_trip_id order by datetime desc) as order_num
        from bus_position) as a
    where order_num = 1
    ''', dbconn)
    del df['order_num']
    del df['the_geom']
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['scheduled_trip_id'] = pd.to_numeric(df['scheduled_trip_id'])
    return df


def call_api():
    # https://developer.wmata.com/Products
    # Default Tier
    # "Rate limited to 10 calls/second and 50,000 calls per day"
    try:
        req = requests.get('http://api.wmata.com/Bus.svc/json/jBusPositions',
                           headers=headers, params=params)
        
        data = json.loads(req.text)
        
        df = pd.DataFrame(data['BusPositions'])
        df.columns = df.columns.str.lower()
        df = df.rename(
            columns={
                'tripid':'scheduled_trip_id', 
                'routeid': 'route_short_name',
                'directionnum':'direction_num',
                'directiontext': 'direction_text',
                'tripendtime': 'trip_end_time',
                'tripstarttime': 'trip_start_time',
                'tripheadsign': 'trip_headsign',
                'vehicleid': 'vehicle_id'
            })
        df['datetime'] = pd.to_datetime(df['datetime'])
        df['scheduled_trip_id'] = pd.to_numeric(df['scheduled_trip_id'])
        return df 
    except Exception as e:
        raise Exception(e)
        logging.error("Error: ".format(str(e)))
        return pd.DataFrame([])

free_limit_gb = 20
def db_size():
    sz= pd.read_sql('''
        SELECT sum( pg_total_relation_size(oid) ) AS total_bytes
          FROM pg_class 
       ''', dbconn)
    return round(float(sz['total_bytes'][0])/(10**9), 2)


def bulk_insert(df, table, schema="public"):
    header = ','.join(df.columns)
    f = StringIO(df.to_csv(index=False))
    f.readline() # remove header
    copy_statement = "COPY {}.{} ({}) FROM STDIN WITH (FORMAT csv);".format(schema, table, header)
    cur.copy_expert(copy_statement, f)
    f.close()
    pg.commit()
    return 0

#%%
n = 0 # TODO: initialize n from db
start_day = dt.now().date()
today = start_day
df = initial()



current_size = db_size()
logging.info("Current db size is {} GB".format(current_size))
#%%

start_time = dt.now()
finish_time = start_time + timedelta(minutes=run_minutes)

logging.info("running for {} minutes (end time = {}), at interval of {} seconds".format(run_minutes, finish_time, interval_seconds))


while dt.now() < finish_time and n < 50000:
    it_start = dt.now()

    df1 = call_api()
    
    """
    the API is called every interval_seconds. the vehicle position
    on certain vehicles may not have been updated since the last call.
    therefore, check using a pandas left join on the response to the
    previous response to see if the datetime has changed.
    only load the new records to the database
    """
    joined = df1.merge(df, how='left', on=['scheduled_trip_id', 'vehicle_id', 'datetime'],
                       suffixes=('','_old'))
    keep_cols = [col for col in joined.columns if col.find('_old')==-1]
    new = joined[pd.isnull(joined['lat_old'])][keep_cols]
    
    df = joined[keep_cols]

    n_pulled = len(df1)
    n_new = len(new)
    n_stale = len(df1) - len(new)
    logging.info('pulled {} records: {} are new, {} are stale records.'.format(n_pulled, n_new, n_stale ))

    cur.execute('truncate table etl.bus_position')
    pg.commit()

    bulk_insert(new, table='bus_position', schema='etl')

    cur.execute('''insert into public.bus_position
        (datetime, deviation, direction_num, direction_text,
         lat, lon, route_short_name, trip_end_time, trip_headsign,
         scheduled_trip_id, trip_start_time, vehicle_id,
         the_geom
        )
        select 
         datetime, deviation, direction_num, direction_text,
         lat, lon, route_short_name, trip_end_time, trip_headsign,
         a.scheduled_trip_id, a.trip_start_time, a.vehicle_id,
         ST_setsrid(ST_makepoint(lon, lat), 4326) as the_geom

        from etl.bus_position 
        ''')
    pg.commit()

    it_end = dt.now()
    sleep_time = (it_end - it_start).total_seconds()
    if sleep_time > 0 and sleep_time <= interval_seconds:
        sleep(interval_seconds - sleep_time) 
    n += 1

    if n % 1000 == 0:
        # check the database is not getting to big every 1000 iterations
        logging.info('Current database size: {}'.format(db_size()))

    
logging.info("Finished")