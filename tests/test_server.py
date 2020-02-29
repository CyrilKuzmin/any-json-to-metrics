from flask import Flask
from flask import Response
import json 

app = Flask(__name__)

@app.route('/<name>')
def hello_name(name):
    data = {}
    with open(name, 'r') as file:
        data = json.load(file)
    resp = Response(json.dumps(data)+'\n', headers={'Content-Type':'application/json'})
    return resp

if __name__ == '__main__':
    app.run()
