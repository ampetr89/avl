from db import Db 
import pandas as pd

db = Db()
pg = db.pg
cur = pg.cursor()


with open('lines_create.sql','r') as f:
	create_sql = f.read()
	cur.execute(create_sql)
	pg.commit()

f = open('osm_line.csv','r')

columns = f.readline().strip()
columns = ','.join(['"'+c+'"' for c in columns.split(',')])
copy_statement = "COPY osm.line ({}) FROM STDIN WITH (FORMAT csv);".format(columns)
print(columns)
cur.copy_expert(copy_statement, f)
pg.commit()
f.close()

