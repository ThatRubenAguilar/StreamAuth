from flask import Flask, request, jsonify
from flask_api import status
import os.path
import urllib.parse as urlparse
import logging

app = Flask(__name__)

publishkey_cache = {}
playkey_cache = {}
live_key = None


def populate_cache(cache, full_file_path):
    if not os.path.isfile(full_file_path):
        app.logger.warning('No keys loaded for {}'.format(full_file_path))
        return

    app.logger.info("loading keys from '{}'".format(full_file_path))
    try:
        with open(full_file_path) as f:
            content = f.readlines()

        content = [x.strip() for x in content]
        for key in content:
            cache[key] = key
    except Exception as e:
        app.logger.error("failed to load keys from '{}' because {}".format(full_file_path, e.args[0]))


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
    if request.form.get('name') is None or request.form.get('swfurl') is None:
        return app.make_response(('Malformed request', status.HTTP_400_BAD_REQUEST))

    stream_key = extract_stream_key(key_arg_name)

    if stream_key is None:
        return app.make_response(('Missing {}'.format(key_arg_name), status.HTTP_400_BAD_REQUEST))

    if stream_key not in key_cache:
        return app.make_response(('Incorrect {}'.format(key_arg_name), status.HTTP_401_UNAUTHORIZED))

    return app.make_response(('OK', status.HTTP_200_OK))


def extract_stream_key(key_arg_name):
    stream_url = urlparse.urlparse(request.form.get('swfurl'))
    stream_url_qs = urlparse.parse_qs(stream_url.query)
    if key_arg_name in stream_url_qs:
        return stream_url_qs[key_arg_name][0]

    if request.form.get(key_arg_name) is not None:
        return request.form.get(key_arg_name)

    return None


@app.errorhandler(Exception)
def handle_invalid_usage(error):
    # rv = dict()
    # rv['message'] = error.message
    # response = jsonify(rv)
    # response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    # return response
    app.logger.error(error.message)
    return app.make_response(('Internal Server Error', status.HTTP_500_INTERNAL_SERVER_ERROR))


if __name__ == '__main__':
    app.logger.setLevel(logging.INFO)
    app.run(host='127.0.0.1', port=5001)
