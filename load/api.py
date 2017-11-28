import requests
import json
from db import Db
# import psycopg2 as pg
import pandas as pd
from time import sleep
from datetime import  datetime as dt
from datetime import timedelta
import logging
import os

import sys

if len(sys.argv) > 1:
    run_minutes = int(sys.argv[1])
else:
    run_minutes = 60 # default to an hour


wd = os.getcwd()
logfile = os.path.join(wd, 'api.log')

logging.basicConfig(format="%(message)s", filename=logfile, 
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

params = {
    # Request parameters
    #'RouteID': 'B30',
    #'Lat': '{number}',
    #'Lon': '{number}',
    #'Radius': '{number}',
}


def initial():
    df = pd.read_sql("""
    select * from 
        (select *, row_number() over (partition by scheduled_trip_id order by datetime desc) as order_num
        from bus_position) as a
    where order_num = 1
    """, dbconn)
    del df['order_num']
    df.set_index(['scheduled_trip_id', 'datetime'], inplace=True)
    return df

def call_api():
    # https://developer.wmata.com/Products
    # Default Tier
    # "Rate limited to 10 calls/second and 50,000 calls per day"
    try:
        req = requests.get('http://api.wmata.com/Bus.svc/json/jBusPositions', headers=headers, params=params)
        
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
        df.set_index(['scheduled_trip_id', 'datetime'], inplace=True) # should be unique by this row
        return df 
    except Exception as e:
        raise Exception(e)
        logging.error("Error: ".format(str(e)))
        return pd.DataFrame([])

free_limit_gb = 20
def db_size():
    sz= pd.read_sql("""
        SELECT sum( pg_total_relation_size(oid) ) AS total_bytes
          FROM pg_class 
       """, dbconn)
    return round(float(sz['total_bytes'][0])/(10**9), 2)

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

logging.info("running for {} minutes (end time = {})".format(run_minutes, finish_time))


while dt.now() < finish_time and n < 50000:

    df1 = call_api()

    
    stale = df1[df1.index.isin(df.index)]
    # only add to the db if the position has been updated (trip id + timestamp is different)
    df1 = df1[~df1.index.isin(df.index)]

    nclean = len(df1)
    df = df1

    #df = df.rename(columns={})
    

    logging.info('{} - {} updated records, {} stale records.'.format(dt.now(), nclean, len(stale) ))

    cur.execute('truncate table etl.bus_position')
    pg.commit()
    
    df.reset_index().drop_duplicates(
            subset=['scheduled_trip_id', 'datetime']).to_sql(
                    'bus_position', dbconn, if_exists='append', 
              schema='etl', index=False)
    
    cur.execute('update etl.bus_position set the_geom = ST_setsrid(ST_makepoint(lon, lat), 4326)')
    pg.commit()
    cur.execute('insert into public.bus_position select * from etl.bus_position')
    pg.commit()
    
    
    sleep(10)
    n += 1
    # today = dt.now().date()

    if n % 1000 == 0:
        logging.info('Current database size: {}'.format(db_size()))

    """
    if today != start_day:
        logging.info('{} - day changed over. Continuing..'.format(dt.now()))
        n = 0
        start_day = today

    elif n==50000:
        logging.info('Hit 50K limit at {}'.format(dt.now()))
        tomorrow = today + timedelta(1)
        time_till_day_end =  mktime(tomorrow.timetuple()) -  mktime(dt.now().timetuple())
        logging.info(' sleeping for {} seconds...'.format(time_till_day_end+1))
        sleep(time_till_day_end + 1)

    current_size = db_size()
    if current_size > 0.8*free_limit_gb:
        # stop when it gets to be 80% of the max allowed size
        logging.info("{} - Stopping load. database size has reached {} GB".format(dt.now(), current_size))
        break
    """
logging.info("Finished")