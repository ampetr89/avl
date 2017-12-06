

/* https://gist.github.com/BenoitDuffez/3f5ebd741802dcae13bf  */
DROP TABLE IF EXISTS gtfs.agency
;

CREATE TABLE gtfs.agency (
    transit_system VARCHAR(50) /* NOT NULL */,
    agency_id VARCHAR(100),
    agency_name VARCHAR(255) /* NOT NULL */,
    agency_url VARCHAR(255) /* NOT NULL */,
    agency_timezone VARCHAR(100) /* NOT NULL */,
    agency_lang VARCHAR(100),
    agency_phone VARCHAR(100),
    agency_fare_url VARCHAR(100),
    PRIMARY KEY (agency_id)
);


DROP TABLE IF EXISTS gtfs.calendar_dates
; 
CREATE TABLE gtfs.calendar_dates (
    /* id SERIAL NOT NULL PRIMARY KEY, */
    transit_system VARCHAR(50) /* NOT NULL */,
    service_id VARCHAR(255) /* NOT NULL */,
    date VARCHAR(8) /* NOT NULL */,
    exception_type SMALLINT /* NOT NULL */
    /*PRIMARY KEY service_id (service_id, exception_type)*/
);
 


DROP TABLE IF EXISTS gtfs.calendar
;
CREATE TABLE gtfs.calendar (
    /* id SERIAL NOT NULL PRIMARY KEY, */
    transit_system VARCHAR(50) /* NOT NULL */,
    service_id VARCHAR(255) /* NOT NULL */,
    monday SMALLINT /* NOT NULL */,
    tuesday SMALLINT /* NOT NULL */,
    wednesday SMALLINT /* NOT NULL */,
    thursday SMALLINT /* NOT NULL */,
    friday SMALLINT /* NOT NULL */,
    saturday SMALLINT /* NOT NULL */,
    sunday SMALLINT /* NOT NULL */,
    start_date VARCHAR(8) /* NOT NULL */,
    end_date VARCHAR(8) /* NOT NULL */
    /*PRIMARY KEY service_id (service_id)*/
);
 

DROP TABLE IF EXISTS gtfs.fare_attributes
;
CREATE TABLE gtfs.fare_attributes (
    /* id SERIAL NOT NULL PRIMARY KEY, */
    transit_system VARCHAR(50) /* NOT NULL */,
    fare_id VARCHAR(100),
    price VARCHAR(50) /* NOT NULL */,
    currency_type VARCHAR(50) /* NOT NULL */,
    payment_method SMALLINT /* NOT NULL */,
    transfers SMALLINT /* NOT NULL */,
    transfer_duration VARCHAR(10),
    exception_type SMALLINT /* NOT NULL */,
    agency_id BIGINT
    /*KEY fare_id (fare_id)*/
);
 

DROP TABLE IF EXISTS gtfs.fare_rules
;
CREATE TABLE gtfs.fare_rules (
    /* id SERIAL NOT NULL PRIMARY KEY, */
    transit_system VARCHAR(50) /* NOT NULL */,
    fare_id VARCHAR(100),
    route_id VARCHAR(100),
    origin_id VARCHAR(100),
    destination_id VARCHAR(100),
    contains_id VARCHAR(100)/*,
    KEY fare_id (fare_id),
    KEY route_id (route_id)*/
);
 

DROP TABLE IF EXISTS gtfs.feed_info
;
CREATE TABLE gtfs.feed_info (
    /* id SERIAL NOT NULL PRIMARY KEY, */
    transit_system VARCHAR(50) /* NOT NULL */,
    feed_publisher_name VARCHAR(100),
    feed_publisher_url VARCHAR(255) /* NOT NULL */,
    feed_lang VARCHAR(255) /* NOT NULL */,
    feed_start_date VARCHAR(8),
    feed_end_date VARCHAR(8),
    feed_version VARCHAR(100)
);
 

DROP TABLE IF EXISTS gtfs.frequencies
;
CREATE TABLE gtfs.frequencies (
    /* id SERIAL NOT NULL PRIMARY KEY, */
    transit_system VARCHAR(50) /* NOT NULL */,
    trip_id VARCHAR(100) /* NOT NULL */,
    start_time VARCHAR(8) /* NOT NULL */,
    end_time VARCHAR(8) /* NOT NULL */,
    headway_secs VARCHAR(100) /* NOT NULL */,
    exact_times SMALLINT/*,
    KEY trip_id (trip_id)*/
);
 

DROP TABLE IF EXISTS gtfs.routes
;
CREATE TABLE gtfs.routes (
    transit_system VARCHAR(50) /* NOT NULL */,
    route_id VARCHAR(100),
    agency_id VARCHAR(50),
    route_short_name VARCHAR(50) /* NOT NULL */,
    route_long_name VARCHAR(255) /* NOT NULL */,
    route_type VARCHAR(2) /* NOT NULL */,
    route_text_color VARCHAR(255),
    route_color VARCHAR(255),
    route_url VARCHAR(255),
    route_desc VARCHAR(255)
    /*    PRIMARY KEY (route_id),
    KEY agency_id (agency_id),
    KEY route_type (route_type),
    CONSTRAINT agency_id FOREIGN KEY (agency_id) REFERENCES agency (agency_id)*/
);
 

DROP TABLE IF EXISTS gtfs.shapes
;
CREATE TABLE gtfs.shapes (
    /* id SERIAL NOT NULL PRIMARY KEY, */
    transit_system VARCHAR(50) /* NOT NULL */,
    shape_id VARCHAR(100) /* NOT NULL */,
    shape_pt_lat DECIMAL(8,6) /* NOT NULL */,
    shape_pt_lon DECIMAL(8,6) /* NOT NULL */,
    shape_pt_sequence SMALLINT /* NOT NULL */,
    shape_dist_traveled VARCHAR(50)/*,
    KEY shape_id (shape_id)*/
);


DROP TABLE IF EXISTS gtfs.stops
;
CREATE TABLE gtfs.stops (
    transit_system VARCHAR(50) /* NOT NULL */,
    stop_id VARCHAR(255),
    stop_code VARCHAR(50),
    stop_name VARCHAR(255) /* NOT NULL */,
    stop_desc VARCHAR(255),
    stop_lat DECIMAL(10,6) /* NOT NULL */,
    stop_lon DECIMAL(10,6) /* NOT NULL */,
    zone_id VARCHAR(255),
    stop_url VARCHAR(255),
    location_type VARCHAR(2),
    parent_station VARCHAR(100),
    stop_timezone VARCHAR(50),
    wheelchair_boarding SMALLINT
        /*PRIMARY KEY (stop_id),
    KEY zone_id (zone_id),
    KEY stop_lat (stop_lat),
    KEY stop_lon (stop_lon),
    KEY location_type (location_type),
    KEY parent_station (parent_station)*/
);
 

DROP TABLE IF EXISTS gtfs.trips
;
CREATE TABLE gtfs.trips (
    transit_system VARCHAR(50) /* NOT NULL */,
    route_id VARCHAR(100) /* NOT NULL */,
    service_id VARCHAR(100) /* NOT NULL */,
    trip_id VARCHAR(255),
    scheduled_trip_id BIGINT,
    trip_headsign VARCHAR(255),
    trip_short_name VARCHAR(255),
    direction_id SMALLINT, /*0 for one direction, 1 for another. */
    block_id VARCHAR(11),
    shape_id VARCHAR(11),
    wheelchair_accessible SMALLINT, /*0 for no information, 1 for at least one rider accommodated on wheel chair, 2 for no riders accommodated. */
    bikes_allowed SMALLINT /* 0 for no information, 1 for at least one bicycle accommodated, 2 for no bicycles accommodated */
        /*PRIMARY KEY (trip_id),
    KEY route_id (route_id),
    KEY service_id (service_id),
    KEY direction_id (direction_id),
    KEY block_id (block_id),
    KEY shape_id (shape_id),
    CONSTRAINT route_id FOREIGN KEY (route_id) REFERENCES routes (route_id),
    CONSTRAINT service_id FOREIGN KEY (service_id) REFERENCES calendar (service_id)*/
);
 


DROP TABLE IF EXISTS gtfs.stop_times
;
CREATE TABLE gtfs.stop_times (
    /* id SERIAL NOT NULL PRIMARY KEY, */
    transit_system VARCHAR(50) /* NOT NULL */,
    trip_id VARCHAR(100) /* NOT NULL */,
    arrival_time VARCHAR(8) /* NOT NULL */,
    arrival_time_seconds BIGINT,
    departure_time VARCHAR(8) /* NOT NULL */,
    departure_time_seconds BIGINT,
    stop_id VARCHAR(100) /* NOT NULL */,
    stop_sequence VARCHAR(100) /* NOT NULL */,
    stop_headsign VARCHAR(50),
    pickup_type VARCHAR(2),
    drop_off_type VARCHAR(2),
    shape_dist_traveled VARCHAR(50)/*,
    KEY trip_id (trip_id),
    KEY arrival_time_seconds (arrival_time_seconds),
    KEY departure_time_seconds (departure_time_seconds),
    KEY stop_id (stop_id),
    KEY stop_sequence (stop_sequence),
    KEY pickup_type (pickup_type),
    KEY drop_off_type (drop_off_type),
    CONSTRAINT trip_id FOREIGN KEY (trip_id) REFERENCES trips (trip_id),
    CONSTRAINT stop_id FOREIGN KEY (stop_id) REFERENCES stops (stop_id) */
);
 

DROP TABLE IF EXISTS gtfs.transfers
;
CREATE TABLE gtfs.transfers (
    /* id SERIAL NOT NULL PRIMARY KEY, */
    transit_system VARCHAR(50) /* NOT NULL */,
    from_stop_id BIGINT /* NOT NULL */,
    to_stop_id VARCHAR(8) /* NOT NULL */,
    transfer_type SMALLINT /* NOT NULL */,
    min_transfer_time VARCHAR(100)
);