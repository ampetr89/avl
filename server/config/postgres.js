// http://mherman.org/blog/2016/03/13/designing-a-restful-api-with-node-and-postgres/#.Wig3lUqnE2w
var promise = require('bluebird')

var options = {
  // Initialization Options
  promiseLib: promise
};


var pgp = require('pg-promise')(options);
const cn = {
    host: 'avl.cgzfeinbmbkk.us-east-1.rds.amazonaws.com',
    port: 5432,
    database: 'avl',
    user: 'api',
    password: '1'
};
//var connectionString = 'api://avl.cgzfeinbmbkk.us-east-1.rds.amazonaws.com:5432/avl';
//var db = pgp(connectionString);
const db = pgp(cn);
module.exports = db;

/*
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

*/