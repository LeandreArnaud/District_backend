import pandas as pd
import json
from flask import Flask, request
from geopy.geocoders import Nominatim
from geopy import distance

config = json.load(open('config.json'))

# df containing restricted db
df = pd.read_csv(config['FILENAME'], index_col=0, dtype=str)
# flask app
app = Flask(__name__)
# geopy geocoder
geolocator = Nominatim(user_agent=config['GEOPY_APP_NAME'])


# util functions
def is_same_street(street, lat, lon):
  # TODO: format: rm accents, spaces, maybe evaluate the % of common char
  # this will work for most french adresses thanks to OSM
  streetName = street.lower().strip()
  location = geolocator.reverse(f"{lat}, {lon}")
  return streetName in location.address.lower().strip()

# routes
@app.route("/")
def homepage():
    return "Welcome to MPV Disctrict app API !", 200
  
# TODO: treat accents
# route to get a random adress
@app.route("/get_random_adress")
def get_random_adress():
    line = df.sample(n=1)
    return {'id': line.ID.values[0],
            'num': line.NUM.values[0],
            'rue': line.RUE.values[0],
            'cp': line.CP.values[0],
            'com': line.COM.values[0]}, 200

# route to evaluate distance
@app.route("/get_evaluation")
def get_evaluation():
    try:
        ID = request.headers.get('ID')
        lat = request.headers.get('lat')
        lon = request.headers.get('lon')

        line = df[df.ID == ID].iloc[0]
        dist = distance.distance([line.LAT, line.LON], [lat, lon]).meters
        score = 0

        # TODO: increase 10m
        # TODO: increase reward based on dist
        if dist < 10:
            score = 1
        elif dist > 1000:
            pass
        else:
            # TODO: add try except
            iss = is_same_street(line.RUE, lat, lon)
            score = iss*0.8 + ((10/dist)**1)*0.2

        return {'distance': round(dist, 0), 
                'score': round(score, 3),
                'lat': float(line.LAT),
                'lon': float(line.LON)}, 200
    except:
        return {'message': 'Invalid ID, lat, or lon provided'}, 400



if __name__ == "__main__":
    app.run(debug=False)