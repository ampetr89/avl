var express = require('express');
var router = express.Router()

var db = require('../../controllers/score');

router.get('/ranking', db.getRanking);


module.exports = router;