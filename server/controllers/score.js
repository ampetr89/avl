db = require('../config/postgres');

function getRanking(req, res, next) {
  db.any(`select * from (select names, count(*) as value
            from gtfs.matched_ways 
            where names is not null
            group by names
            order by value desc
            limit 25) as a order by value asc`)
    .then(function (data) {
      res.status(200)
        .json({
          status: 'success',
          data: data,
          message: 'Retrieved road rankings'
        });
    })
    .catch(function (err) {
      return next(err);
    });
}

module.exports = {
  getRanking: getRanking
};