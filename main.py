import requests
import os
import json
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
load_dotenv()

ENV_TYPE = os.environ.get('ENV_TYPE')

print('ENV_TYPE: ', ENV_TYPE)

PROD_ORIGIN = 'https://webmporium.com'
DEV_ORIGIN = 'http://localhost:3005'

if ENV_TYPE == 'dev':
    origin = DEV_ORIGIN
else:
    origin = PROD_ORIGIN

print('origin: ', origin)

app = Flask(__name__)
# api = Api(app)
# cors = CORS(app, resources={r"/*": {"origins": "https://rxbuddy.net"}})
cors = CORS(app, resources={r"/*": {"origins": origin}})

@app.route('/status', methods = ['GET'])
def status():
    return {
        'status': 'ok'
    }, 200

@app.route('/generatemv', methods=['POST'])
def generatemv():
    postData = json.loads(request.data)
    print('post request body: ', postData)
    threadURL = postData['thread_url']
    spotifyURL = postData['spotify_url']
    return {
        'success': True
    }, 200

print('---------------------------------------')

if __name__ == '__main__':
    app.run(debug=True)  # run our Flask app