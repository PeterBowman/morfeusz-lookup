import os
from flask import Flask, request
from morfeusz import process_request
from concraft_pl2 import Concraft, Server

app = Flask(__name__)

model_path = os.environ.get('CONCRAFT_PL_MODEL')
concraft_path = os.environ.get('CONCRAFT_PL_EXECUTABLE')

if model_path is not None and concraft_path is not None:
    server = Server(concraft_path=concraft_path, model_path=model_path)
    concraft = Concraft()
else:
    server = None
    concraft = None

@app.route('/api')
def api():
    params = request.get_json() if request.is_json else request.args

    try:
        return process_request(params, concraft)
    except BaseException as e:
        return {'errors': ['%s: %s' % (type(e).__name__, str(e))]}

if __name__ == '__main__':
    try:
        app.run()
    finally:
        if server is not None: server.terminate()
