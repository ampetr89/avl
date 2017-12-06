const session = require('express-session');
const cookieParser = require('cookie-parser');

var bodyParser = require('body-parser');
var express = require( "express");
var path = require( "path");


var app = express();

const sessionConfig = {
  saveUninitialized: true, // as soon as they visit the site (regardless whether they've logged in), create a cookie
  secret: 'lksjdgkjg',
  resave: false,
  name: 'session', // can be seen in the browser
  rolling: true,
  cookie: {
    secure: false, // should be true on a production server!!
    httpOnly: false,
    maxAge: 360000 // expires after 100 hours? 
  }
}

app.use(cookieParser('lkjljlkdfgdfgj')); // cookie encryption
app.use(session(sessionConfig));


// app.use(express.static(path.join(__dirname + "./public")));
app.use(bodyParser.json())
   .use(bodyParser.urlencoded({extended: true})); 


// require the postgres configuration file
//require('./server/config/postgres');


// set up static file path 
app.use(express.static(path.join(__dirname, '/public/dist')));


// set up routes
app.use('/api/score', require('./server/config/routes/score'));


app.use(require('./server/config/routes/catchall'))



app.listen(8000, function() {
 console.log("listening on port 8000"); 
});
