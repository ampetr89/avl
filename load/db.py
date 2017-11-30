from sqlalchemy import create_engine
import psycopg2 as pg
import os

class Db():
	def __init__(self):
		url = 'postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}'

		path = os.path.dirname(os.path.abspath(__file__))
		with open(os.path.join(path,'password.txt'), 'r') as f:
			pw = f.read().strip()
		# http://initd.org/psycopg/docs/module.html
		# modify this to use your own credentials and database:
		params = {
			'user':'postgres',
	        'password': pw, # this is the password we got from the user above
	        'host':'avl.cgzfeinbmbkk.us-east-1.rds.amazonaws.com',
	        'port':'5432',
	        'dbname':'avl'  # name of the database on the server
		}
		formatted_url = url.format(**params)
		self.conn = create_engine(formatted_url)
		self.pg = pg.connect(**params)
		
		del params['password']
		self.params = params

