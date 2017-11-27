const pg = require('pg');
var fs = require('fs');
var path = require('path');
const reg = new RegExp('\\.js$', 'i')


// TODO make db user called app with SELECT priv and no password.
// database is IP protected so dont need a user password

//const client = new pg.Client(connectionString);
const client = new pg.Client({
  user: 'app',
  host: 'avl.cgzfeinbmbkk.us-east-1.rds.amazonaws.com',
  database: 'avl',
  port: 5432,
})
client.connect();


var models_path = path.join(__dirname, './../models');

///mongoose.Promise = global.Promise; // for postgres???

// read all of the files in the models_path and require (run) each of the javascript files
// readdirSync ensures the files have been run before you read them(?)
fs.readdirSync(models_path).forEach(function(file) {
  if(reg.test(file)){
    require(path.join(models_path, file));
  }
});

/*
const query = client.query(
  'CREATE TABLE items(id SERIAL PRIMARY KEY, text VARCHAR(40) not null, complete BOOLEAN)');
query.on('end', () => { client.end(); });
*/