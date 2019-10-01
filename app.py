# Climate App
##############################################

import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect, and_, or_, desc

from flask import Flask, jsonify

import datetime as dt
from dateutil.relativedelta import relativedelta

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurements = Base.classes.measurement
Stations = Base.classes.station


# 2. Create an app, being sure to pass __name__
app = Flask(__name__)

session = Session(engine)
last_date = session.query(func.max(Measurements.date)).first()[0]
last_date = dt.datetime.strptime(last_date, '%Y-%m-%d')
print(last_date)
#extract year, month, and day as integers
last_year = int(dt.datetime.strftime(last_date, '%Y'))
last_month = int(dt.datetime.strftime(last_date, '%m'))
last_day = int(dt.datetime.strftime(last_date, '%d'))

#calculate one year before latest date
dt_year_before = dt.date(last_year, last_month, last_day) - relativedelta(months=12)
dt_year_before = dt.datetime.strftime(dt_year_before, '%Y-%m-%d')

session.close()

# 3. Define what to do when a user hits the index route
@app.route("/")
def welcome():
    print("Server received request for 'Home' page...")

    # """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"------------------------------------------------<br/>"
        f"Precipitation data for last year.<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"------------------------------------------------<br/>"
        f"List of all the stations.<br/>"
        f"/api/v1.0/stations<br/>"
        f"------------------------------------------------<br/>"
        f"Lists Temperature data for last year.<br/>"
        f"/api/v1.0/tobs<br/>"
        f"------------------------------------------------<br/>"

        f"For following routes, Date Format: YYYY-MM-DD.<br/>"
        f"------------------------------------------------<br/>"
        f"Lists min, max and average temprature for the given date and each date after.<br/>"
        f"/api/v1.0/start_date<br/>"
        f"Lists min, max and average temprature for each date between the given start and end date.<br/>"
        f"/api/v1.0/start_date/end_date"
    )


# Get precipitation data
# Convert the query results to a Dictionary using date as the key and prcp as the value.
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of precipitation with date"""

    sel = [Measurements.date,
        Measurements.prcp,
        Measurements.station]

    results = session.query(*sel).\
            filter(and_(Measurements.date <= last_date, Measurements.date >= dt_year_before)).\
            order_by(Measurements.date).all()

    prcp_dates = []

    for result in results:
        prcp_dict = {}
        prcp_dict[result[0]] = result[1]
        prcp_dict["Station"] = result[2]
        prcp_dates.append(prcp_dict)
    session.close()

    return jsonify(prcp_dates)

# Get a list of stations
@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    results = session.query(Stations.name).all()

    # # Convert into normal list
    stations = list(np.ravel(results))

    session.close()

    return jsonify(stations)

# get the temerature data for the previous year.
@app.route("/api/v1.0/tobs")
def temp_obsv():
    session = Session(engine)

    results = session.query(Measurements.date, Measurements.tobs, Measurements.station).\
        filter(and_(Measurements.date>=dt_year_before, Measurements.date<=last_date)).\
        order_by(Measurements.date).all()   

    tob_list = []
    for result in results:
        tob_data = {}
        tob_data[result[0]] = result[1]
        tob_data["Station"] = result[2]
        tob_list.append(tob_data)

    session.close()

    return jsonify(tob_list)

# Get the min, max and avg tempreture for the given date and greater than the given date
@app.route("/api/v1.0/<start_date>")
def temp_stat(start_date):
    try:
        if start_date != dt.datetime.strptime(start_date, "%Y-%m-%d").strftime('%Y-%m-%d'):
            raise ValueError
        session = Session(engine)
        results = session.query(Measurements.date, func.min(Measurements.tobs),\
                        func.max(Measurements.tobs), func.avg(Measurements.tobs)).\
                        filter(func.strftime("%Y-%m-%d", Measurements.date)>= start_date).\
                        group_by(Measurements.date).all()
        temp_startdt = []
        for result in results:
            temp_start_dict = {}
            temp_start_dict["Date"] = result[0]
            temp_start_dict["Min Temp"] = result[1]
            temp_start_dict["Max Temp"] = result[2]
            temp_start_dict["Avg Temp"] = result[3]
            temp_startdt.append(temp_start_dict)

        session.close()
        return jsonify(temp_startdt)
    except ValueError:
        return("Please enter the date in YYYY-MM-DD format.")

# Get the min, max and avg tempreture for the days between the start date and end date.
@app.route("/api/v1.0/<start_date>/<end_date>")
def temp_stat_end(start_date,end_date):
    try:
        if (start_date != dt.datetime.strptime(start_date, "%Y-%m-%d").strftime('%Y-%m-%d')\
            or end_date != dt.datetime.strptime(end_date, "%Y-%m-%d").strftime('%Y-%m-%d')):
            raise ValueError
        session = Session(engine)
        results = session.query(Measurements.date, func.min(Measurements.tobs),\
                        func.max(Measurements.tobs), func.avg(Measurements.tobs)).\
                        filter(and_(Measurements.date >= start_date, Measurements.date <= end_date)).\
                        group_by(Measurements.date).all()
        temp_start_end_dt = []
        for result in results:
            temp_start_end_dict = {}
            temp_start_end_dict["Date"] = result[0]
            temp_start_end_dict["Min Temp"] = result[1]
            temp_start_end_dict["Max Temp"] = result[2]
            temp_start_end_dict["Avg Temp"] = result[3]
            temp_start_end_dt.append(temp_start_end_dict)

        session.close()
        return jsonify(temp_start_end_dt)
    except ValueError:
        return("Please enter the date in YYYY-MM-DD format.")

if __name__ == "__main__":
    app.run(debug=True)