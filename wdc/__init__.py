from flask import Flask
from flask import request

import json
import redis
from boxsdk import OAuth2, Client
from boxsdk.exception import BoxOAuthException

from settings import (CLIENT_ID, CLIENT_SECRET, REDIS_HOST, REDIS_PORT)

from contextlib import contextmanager

import logging

from settings import INDEX


PROJECT_PATH = INDEX

app = Flask(__name__)
app.config.from_object("settings")

oauth = OAuth2(client_id=CLIENT_ID,
               client_secret=CLIENT_SECRET)

def clear_tokens(session):
    logging.info("Clear tokens")
    for token in ('access_token', 'refresh_token'):
        session[token] = ""

@contextmanager
def get_client(session):

    try:
        def store_tokens(access_token, refresh_token):
            session['access_token'] = access_token
            session['refresh_token'] = refresh_token

        oauth = OAuth2(client_id=CLIENT_ID,
                       client_secret=CLIENT_SECRET,
                       access_token=session.get('access_token'),
                       refresh_token=session.get('refresh_token'),
                       store_tokens=store_tokens)
        yield Client(oauth)
    except BoxOAuthException as e:
        logging.error("User not authorized: {}".format(e))
        clear_tokens(session)
    except Exception as e:
        logging.error("Custom error: {}".format(e))
        clear_tokens(session)


class RedisHelper:

    def __init__(self):
        pool = redis.ConnectionPool(host=REDIS_HOST,
                                    port=REDIS_PORT,
                                    db=0)
        self._redis_server = redis.StrictRedis(connection_pool=pool)
        self._access_token = None
        self._refresh_token = None

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        self._access_token = value

    @property
    def refresh_token(self):
        return self._access_token

    @refresh_token.setter
    def refresh_token(self, value):
        self._refresh_token = value

    def sync(self, path):
        tokens = json.dumps(dict(access_token=self.access_token,
                                 refresh_token=self.refresh_token))
        self._redis_server.set(path, tokens)

    def get(self, path):
        tokens = self._redis_server.get(path)
        if tokens:
            tokens = json.loads(tokens)
            return tokens.get("access_token"), tokens.get("refresh_token")
        return None, None

from views import index

