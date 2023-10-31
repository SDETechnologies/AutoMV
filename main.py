import requests
import os
import json
import pandas as pd
import urllib.request
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS, cross_origin

ENV_TYPE = os.environ.get('ENV_TYPE')

PROD_ORIGIN = 'https://webmporium.com'
DEV_ORIGIN = 'http://localhost:3005'

if ENV_TYPE == 'dev':
    origin = DEV_ORIGIN
else:
    origin = PROD_ORIGIN

print('origin: ', origin)

app = Flask(__name__)
api = Api(app)
# cors = CORS(app, resources={r"/*": {"origins": "https://rxbuddy.net"}})
cors = CORS(app, resources={r"/*": {"origins": origin}})

@app.route('/status', methods = ['GET'])
def status():
    return {
        'status': 'ok'
    }, 200

print('---------------------------------------')

if __name__ == '__main__':
    app.run()  # run our Flask app