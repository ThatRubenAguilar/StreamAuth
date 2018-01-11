from flask import Flask, request, jsonify
from flask.ext.api import status
from werkzeug.contrib.cache import SimpleCache
import os.path
app = Flask(__name__)


publishkey_cache = SimpleCache()
playkey_cache = SimpleCache()


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
    return 'up'


@app.route('/on_publish', methods=['POST'])
def publish_start():
    return check_auth(publishkey_cache)


@app.route('/on_play', methods=['POST'])
def play_start():
    return check_auth(playkey_cache)


def check_auth(key_cache):
    if request.args.get('name') is None:
        return 'Malformed request', status.HTTP_400_BAD_REQUEST

    stream_key = request.args.get('name')

    if not key_cache.has(stream_key):
        return 'Incorrect credentials', status.HTTP_401_UNAUTHORIZED

    return 'OK', status.HTTP_200_OK


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