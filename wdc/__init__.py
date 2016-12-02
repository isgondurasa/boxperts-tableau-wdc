from flask import Flask

import redis
import json

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


class Data(object):

    def __init__(self, data):
        self.data = data

    def prepare(self, data):
        raise NotImplementedError

class Col(Data):

    def prepare(self):
        result = [
            {
                "id": "file_name",
                "alias": "File Name",
                "type": "string",
                "columnRole": "dimension"
            }
        ]

        for col in self.data['fields']:
            item = {
                "id": col['key'],
                "alias": col['displayName'],
                'type': col['type']
            }

            if item['type'] != 'float':
                item['columnRole'] = 'dimension'

            result.append(item)

        return result


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
        self._folder = None
        self._template = None

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

    @property
    def folder(self):
        return self._folder

    @folder.setter
    def folder(self, value):
        self._folder = value

    @property
    def template(self):
        return self._template

    @template.setter
    def template(self, value):
        self._template = value

    def update(self, path, **params):
        data = self.get(path)
        for k, v in params.items():
            setattr(self, k, v)
        self.sync(path)

    def sync(self, path):
        data = dict(access_token=self.access_token,
                    refresh_token=self.refresh_token,
                    folder=self.folder,
                    template=self.template)
        tokens = json.dumps(data)
        self._redis_server.set(path, tokens)

    def get(self, path):
        data = self._redis_server.get(path)
        if data:
            data = json.loads(data)

            for k, v in data.items():
                setattr(self, k, v)

            return data.get("access_token"), data.get("refresh_token")
        return None, None


def insert_tokens_into_session(session):

    r = RedisHelper()
    access_token, refresh_token = r.get(PROJECT_PATH)
    if not session and (access_token and refresh_token):
        session['access_token'] = access_token
        session['refresh_token'] = refresh_token


def clear_tokens(session):
    logging.info("Clear tokens")
    for token in ('access_token', 'refresh_token'):
        session[token] = ""


from views import index
