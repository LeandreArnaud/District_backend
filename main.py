import pandas as pd
import json
import pyrebase
from flask import Flask, request
from flask import jsonify
from geopy.geocoders import Nominatim
from geopy import distance
from functools import wraps




config = json.load(open('config.json'))


# df containing restricted db
df = pd.read_csv(config['FILENAME'], index_col=0, dtype=str)
# flask app
app = Flask(__name__)
# geopy geocoder
geolocator = Nominatim(user_agent=config['GEOPY_APP_NAME'])
# Connect to firebase
firebase = pyrebase.initialize_app(config['firebase'])
auth = firebase.auth()


# util functions
def is_same_street(street, lat, lon):
  # TODO: format: rm accents, spaces, maybe evaluate the % of common char
  # this will work for most french adresses thanks to OSM
  streetName = street.lower().strip()
  location = geolocator.reverse(f"{lat}, {lon}")
  return streetName in location.address.lower().strip()


# decorator to check token
def check_token(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if not request.headers.get('authorization'):
            return {'message': 'No token provided'},400
        try:
            user = auth.get_account_info(request.headers['authorization'])
            # for later use
            #request.user = user
        except Exception as e: 
            #print(e)
            return {'message':'Invalid token provided.'},400
        return f(*args, **kwargs)
    return wrap


# routes
@app.route("/")
def homepage():
    return "Welcome to MPV Disctrict app API !", 200





# Api route to get a new token for a valid user
@app.route('/token', methods = ['POST'])
def token():
    email = request.form.get('email')
    password = request.form.get('password')
    try:
        user = auth.sign_in_with_email_and_password(email, password) 
        return {'token': user['idToken'], 'refreshToken':user['refreshToken']}, 200
    except:
        return {'message': 'There was an error logging in'}, 400



# Api route to get a new token for a valid user
@app.route('/signup', methods = ['POST'])
def signup():
    email = request.form.get('email')
    password = request.form.get('password')
    try:
        user = auth.create_user_with_email_and_password(email, password)
        return {'token': user['idToken'], 'refreshToken':user['refreshToken']}, 200
    except:
        return {'message': 'There was an error signing up'}, 400


  
# TODO: treat accents
@app.route("/get_random_adress")
@check_token
def get_random_adress():
    line = df.sample(n=1)
    return {'id': line.ID.values[0],
            'num': line.NUM.values[0],
            'rue': line.RUE.values[0],
            'cp': line.CP.values[0],
            'com': line.COM.values[0]}, 200


@app.route("/get_evaluation")
@check_token
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

        return {'distance': dist, 
                'score':score}, 200
    except:
        return {'message': 'Invalid ID, lat, or lon provided'}, 400



if __name__ == "__main__":
    app.run(debug=False)