from flask import Flask, request, jsonify
from flask.ext.api import status
from werkzeug.contrib.cache import SimpleCache
import os.path
app = Flask(__name__)


publishkey_cache = SimpleCache()
playkey_cache = SimpleCache()
live_key = None


def populate_cache(cache, full_file_path):
    if not os.path.isfile(full_file_path):
        print('Warning: No keys loaded for {}'.format(full_file_path))
        return

    with open(full_file_path) as f:
        content = f.readlines()

    content = [x.strip() for x in content]
    for key in content:
        cache.add(key, key)


populate_cache(publishkey_cache, 'publish_keys.txt')
populate_cache(playkey_cache, 'play_key.txt')


@app.route('/server_status', methods=['GET'])
def hello_world():
    return app.make_response(('up', status.HTTP_200_OK))


@app.route('/on_publish', methods=['POST'])
def publish_start():
    return check_auth(publishkey_cache, 'publish_key')


@app.route('/on_play', methods=['POST'])
def play_start():
    return check_auth(playkey_cache, 'play_key')


def check_auth(key_cache, key_arg_name):
    if request.form.get('name') is None or request.form.get('swfurl') is None or request.args.get(key_arg_name) is None:
        return app.make_response(('Malformed request', status.HTTP_400_BAD_REQUEST))

    stream_key = request.args.get(key_arg_name)

    if not key_cache.has(stream_key):
        return app.make_response(('Incorrect {}'.format(key_arg_name), status.HTTP_401_UNAUTHORIZED))

    return app.make_response(('OK', status.HTTP_200_OK))


@app.errorhandler(Exception)
def handle_invalid_usage(error):
    rv = dict()
    rv['message'] = error.message
    response = jsonify(rv)
    response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return response
    #return 'Internal Server Error', status.HTTP_500_INTERNAL_SERVER_ERROR


if __name__== '__main__':
    app.run()