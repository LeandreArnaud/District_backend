import pandas as pd
import json
from flask import Flask, request
from geopy import distance
import requests

config = json.load(open('config.json'))

# df containing restricted db
df = pd.read_csv(config['FILENAME'], index_col=0, dtype=str)
# flask app
app = Flask(__name__)


# util functions
def normalize_streetname(streetName):
    return streetName.lower().strip().replace('-', '').replace(' ', '').replace(',', '')

def is_same_street(street, lat, lon):
  # TODO: format: rm accents, spaces, maybe evaluate the % of common char
  PARAMS = {
    'at': '{},{}'.format(lat, lon),
    'apikey': config['HERE_API_GEOCODE_SECRET']
    }
  rep = requests.get(url = config['HERE_API_GEOCODE_URL'], params = PARAMS).json()

  try:
    return normalize_streetname(street) in normalize_streetname(rep['items'][0]['title'])
  except:
    return False

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
                'lat': round(float(line.LAT), 9),
                'lon': round(float(line.LON), 9)}, 200
    except Exception as e:
        return {'message': 'Invalid ID, lat, or lon provided'}, 400



if __name__ == "__main__":
    app.run(debug=False)