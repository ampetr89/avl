from flask import Flask, request, redirect, render_template
from flask.json import jsonify
from model import *

app = Flask(__name__)

@app.route('/')
def home():
	# routes = get_routes()
	routes = ['B30', '42']
	context = {"routes": routes}
	return render_template('index.html', **context)


@app.route('/gps/<route_name>', methods=['GET']) 
def gps(route_name):
	print('getting gps for', route_name)
	gps_data = get_gps(route_name)
	return jsonify({'data': gps_data})


@app.route('/shape/<source>/<route_name>', methods=['GET']) 
def shape(source, route_name):
	print('getting shape for {} ({})'.format(route_name, source))
	if source=='gtfs':
		route_data = get_gtfs_shape(route_name)
	elif source=='matched':
		route_data = get_matched_shape(route_name)
	
	return jsonify({'data': route_data})


app.run(debug=True) 