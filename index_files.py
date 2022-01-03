from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import sys
import json
import os
import requests

es = Elasticsearch([{'host': 'localhost'}])

encoder_url = 'http://127.0.0.1:8000/encode'

def load_json(filename):
    " Use a generator, no need to load all in memory"
    #for filename in os.listdir(directory):
    #    if filename.endswith('.json'):
    with open(filename,'r') as open_file:
        for report in json.load(open_file).get('reports'):
            
            # add embedding
            res = requests.post(encoder_url, data=json.dumps({'text': report['description']}))
            report['embedding'] = res.json()['embedding']

            #print(report.keys())
            yield report

bulk(es, load_json('geoss_open_resp.json'), index='geoss-test2')
#load_json('geoss_open_resp.json')