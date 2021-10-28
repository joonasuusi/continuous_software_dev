from flask import Flask, render_template, request
import os
from google.cloud import datastore
import time
from datetime import datetime
from datetime import timezone
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace.samplers import ProbabilitySampler
from flask_babel import Babel

# Setup logging object for current context:
logger = logging.getLogger(__name__)

# Add azure loghandler. TODO: Set to _your_ connection string.
connection_string = "InstrumentationKey=0656fc6a-9390-4545-ac9c-d85891971baf;IngestionEndpoint=https://northeurope-0.in.applicationinsights.azure.com/"
logger.addHandler(AzureLogHandler(connection_string=connection_string))

# Define basic config, which sets the handler to print into console by default
logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)

# initialize flaskmiddleware
FlaskMiddleware(
    app,
    exporter=AzureExporter(connection_string=connection_string),
    sampler=ProbabilitySampler(rate=1.0),
)


# Load configs
app.config.from_pyfile("default_config.py")
# silent param allows missing config files.
app.config.from_pyfile("instance_config.py", silent=True)

datastore_client = datastore.Client("beemapkimura")

#Checks if the count of hive locations are > 0
paikat = []
for latlng in datastore_client.query(kind="HiveLocation").fetch():
        paikat.append({
            "lat": latlng['LatLng']['latitude'],
            "lon": latlng['LatLng']['longitude'],
        })
location_count = len(paikat)
if location_count > 0:
    logger.debug("Found %d HiveLocation entries for map." %location_count)
else:
    logger.warn("No hive locations found.")

#Enabling localization
Babel(app)

# main route
@app.route('/')
def home():
    locations = []
    places = []
    for latlng in datastore_client.query(kind="HiveLocation").fetch():
        locations.append({
            "lat": latlng['LatLng']['latitude'],
            "lon": latlng['LatLng']['longitude'],
        })
        places.append({
            "loc": latlng['location']
        })
    print(locations)
    return render_template('mymap.html', hive_locations=locations, places_loc=places)

# set the route to get the data by http post method.
# save_database function gets the data by route and post method
# and send the data to the datastore.
# print methods are temporary methods to assure the data is retrieved from front end.
@app.route('/save', methods=['POST'])
def save_database():
    data = request.data.decode()
    kind = 'HiveLocation'
    splitted_str = data.split("|")
    time = datetime.now()
    time.replace(tzinfo=timezone.utc)
    time_now = time.strftime('%Y-%m-%d-%H:%M:%S')
    task_key = datastore_client.key(kind, time_now)
    task = datastore.Entity(key=task_key)
    splstr = splitted_str[1]+" "+splitted_str[2]
    res = tuple(map(float, splstr.split(" "))) 
    task['LatLng'] = {
        "latitude": round(res[0],4),
        "longitude": round(res[1], 4)
    }
    task['location'] = splitted_str[0]
    task['first name'] = splitted_str[3]
    task['last name'] = splitted_str[4]
    task['email'] = splitted_str[5]
    task['sponsor'] = splitted_str[6]
    datastore_client.put(task)
    return home()

if __name__ == '__main__':
    host = os.getenv("HOST", "127.0.0.1")
    port = os.getenv("PORT", "5000")

    app.run(host=host, port=port)


