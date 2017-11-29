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
import sys

if len(sys.argv) > 1:
    run_minutes = int(sys.argv[1])
else:
    run_minutes = 60 # default to an hour


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

params = {
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
    #df.set_index(['scheduled_trip_id', 'datetime'], inplace=True)
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
        #df.set_index(['scheduled_trip_id', 'datetime'], inplace=True) # should be unique by this row
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


def check_for_dupes():
    dupes = pd.read_sql('''
        select scheduled_trip_id, datetime, count(*)
        from bus_position
        group by 1,2
        having count(*) > 1
        ''', dbconn)
    return dupes

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

logging.info("running for {} minutes (end time = {})".format(run_minutes, finish_time))

interval_seconds = 5 ## TODO: make the interval_seconds a command line arg
while dt.now() < finish_time and n < 50000:
    it_start = dt.now()

    df1 = call_api()
    # print("n = {}".format(n))
    
    joined = df1.merge(df, how='left', on=['scheduled_trip_id', 'datetime'],
                       suffixes=('','_old'))
    keep_cols = [col for col in joined.columns if col.find('_old')==-1]
    new = joined[pd.isnull(joined['lat_old'])][keep_cols]
    
    df = joined[keep_cols]
    """
    stale = df1[df1.index.isin(df.index)]
    # only add to the db if the position has been updated (trip id + timestamp is different)
    new = df1[~df1.index.isin(df.index)] # this now **only has the new values**

    nclean = len(df1)
    """
    """
    new = pd.concat([df, df1], ignore_index =True).\
        drop_duplicates(subset=['scheduled_trip_id', 'datetime'], keep=False)
    df = pd.concat([df, df1]).drop_duplicates(subset=['scheduled_trip_id', 'datetime'])
    """

    n_pulled = len(df1)
    n_new = len(new)
    n_stale = len(df1) - len(new)
    logging.info('pulled {} records: {} are new, {} are stale records.'.format(n_pulled, n_new, n_stale ))

    cur.execute('truncate table etl.bus_position')
    pg.commit()
    
    """
    new.reset_index().drop_duplicates(
            subset=['scheduled_trip_id', 'datetime']).to_sql(
                    'bus_position', dbconn, if_exists='append', 
              schema='etl', index=False)
    """
    #new.to_sql('bus_position', dbconn, if_exists='append', 
    #          schema='etl', index=False)
    bulk_insert(new, table='bus_position', schema='etl')

    cur.execute('update etl.bus_position set the_geom = ST_setsrid(ST_makepoint(lon, lat), 4326)')
    pg.commit()
    
    cur.execute('''insert into public.bus_position
                select *
                from etl.bus_position ''')
    pg.commit()
    
    
    dupes = check_for_dupes()
    if len(dupes) > 0:
        logging.error("duplicate records found!")
        dupes.to_csv("dupes.csv")
        df.to_csv("dupes_df.csv")
        df1.to_csv("dupes_df1.csv")
        raise Exception("duplicates found")

    it_end = dt.now()
    sleep_time = (it_end - it_start).total_seconds()
    if sleep_time > 0:
        sleep(sleep_time) 
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