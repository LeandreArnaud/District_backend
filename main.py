import json
from flask import Flask, request
from geopy import distance
import requests
import mysql.connector

config = json.load(open('config.json'))


# flask app
app = Flask(__name__)
# MySQL connection
cnx = mysql.connector.connect(
    user=config['SQL_USER'],
    password=config['SQL_PASSWORD'], 
    host=config['SQL_SERVER'], 
    port=config['SQL_PORT']
)
# Get a cursor
cur = cnx.cursor()


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
    try:
        coms = request.headers.get('coms')
        cols = ["ID", "NUM", "RUE", "CP", "COM", "RUE_NORM", "COM_NORM"]
        cols_str = str(cols).replace('[', '').replace(']', '').replace("'", '')
        coms_str = str(coms).replace('[', '').replace(']', '')

        cur.execute(f"SELECT {cols_str} FROM District.bano WHERE COM_NORM IN ({coms_str}) ORDER BY RAND() LIMIT 1")
        row = cur.fetchone()
        rep = dict(zip(cols, row))
        return {'id': rep['ID'],
                'num': rep['NUM'],
                'rue': rep['RUE'],
                'cp': rep['CP'],
                'com': rep['COM'],
                'com': rep['RUE_NORM'],
                'com': rep['COM_NORM'],}, 200
    except Exception as e:
        return {'message': 'Invalid communes provided'}, 400


# route to evaluate distance
@app.route("/get_evaluation")
def get_evaluation():
    try:
        ID = request.headers.get('ID')
        lat = request.headers.get('lat')
        lon = request.headers.get('lon')

        cols = ["LAT", "LON", "RUE"]
        cols_str = str(cols).replace('[', '').replace(']', '').replace("'", '')
        cur.execute(f'SELECT {cols_str} FROM District.bano WHERE ID="{ID}" LIMIT 1')
        row = cur.fetchone()
        rep = dict(zip(cols, row))
        
        dist = distance.distance([rep['LAT'], rep['LON']], [lat, lon]).meters
        score = 0

        # TODO: increase 10m
        # TODO: increase reward based on dist
        if dist < 10:
            score = 1
        elif dist > 1000:
            pass
        else:
            # TODO: add try except
            iss = is_same_street(rep['RUE'], lat, lon)
            score = iss*0.8 + ((10/dist)**1)*0.2

        return {'distance': round(dist, 0), 
                'score': round(score, 2),
                'lat': round(rep['LAT'], 9),
                'lon': round(rep['LON'], 9)}, 200
    except Exception as e:
        return {'message': 'Invalid ID, lat, or lon provided'}, 400


# TODO: add departments
# route to get all communes
@app.route("/get_coms")
def get_coms():
    try:
        cur.execute(f'SELECT DISTINCT COM, COM_NORM, CP FROM District.bano')
        coms = cur.fetchall()

        return json.dumps(coms), 200
    except Exception as e:
        return {'message': 'Impossible to get communes'}, 400




if __name__ == "__main__":
    app.run(debug=False)