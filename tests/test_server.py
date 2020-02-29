from flask import Flask
from flask import Response
import json 
import os

app = Flask(__name__,)

@app.route('/<name>')
def hello_name(name):
    data = {}
    with open(name, 'r') as file:
        data = json.load(file)
    resp = Response(json.dumps(data)+'\n', headers={'Content-Type':'application/json'})
    return resp

if __name__ == '__main__':
    files = []
    for file in os.listdir("."):
        if file.endswith(".json"):
            files.append(os.path.join("http://localhost:5000/", file))
    print(f'''
    Test server for any-json-to-metrics exporter
    I've found these JSONs:
    --------------------------------------
    "endpoints": {str(files).replace("'", '"')}
    --------------------------------------
    Paste it in you 'exporter.json' config file
    ''')
    app.run(host="0.0.0.0")
