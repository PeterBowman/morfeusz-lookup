from flask import Flask, request
from morfeusz import process_request

app = Flask(__name__)

@app.route('/api')
def api():
    params = request.get_json() if request.is_json else request.args

    try:
        return process_request(params)
    except BaseException as e:
        return {'errors': ['%s: %s' % (type(e).__name__, str(e))]}

if __name__ == '__main__':
    app.run()
