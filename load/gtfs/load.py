import os
import pandas as pd 
from db import Db

tables = [fname[:-4] for fname in os.listdir('wmata')]
tables = [t for t in tables if t not in ['too_fast', 'route_xref']]

db = Db()
pg = db.pg
cur = pg.cursor()

print(pg)


for tab in tables:
	cur.execute('truncate table gtfs.{}'.format(tab))
	pg.commit()

	f = open('wmata/{}.txt'.format(tab), 'r')
	header = f.readline().strip()
	header = header.replace('"','')
	
	copy_statement = "COPY gtfs.{} ({}) FROM STDIN WITH (FORMAT csv);".format(tab, header)
	print(copy_statement)
	cur.copy_expert(copy_statement, f)
	f.close()
	pg.commit()


print("Finished loading")