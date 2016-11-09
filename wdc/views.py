#! coding: utf-8
# views.py

import json

from wdc import app, oauth, get_client, RedisHelper, PROJECT_PATH
from box import BoxHelper

from flask import render_template, request, redirect, make_response, session

import logging

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


def insert_tokens_into_session():
    r = RedisHelper()
    access_token, refresh_token = r.get(PROJECT_PATH)
    if not session:
        session['access_token'] = access_token
        session['refresh_token'] = refresh_token

@app.route("/")
def index():
    # TODO: make class-based index with support of dynamic project naming


    if not session:
        insert_tokens_into_session()


    title = "BOXWIZARDS tableau WDC"
    try:
        with get_client(session) as client:

           box = BoxHelper(client)

           metafields = box.get_scope_templates_or_none()
           folders = box.get_folder().item_collection['entries']
           return render_template("index.html",
                                  metafields=metafields,
                                  folders=folders,
                                  title=title)

    except Exception as e:
        logging.exception(e)

    auth_url, csrf_token = oauth.get_authorization_url("")
    logging.info("AUTH URL: {}".format(auth_url))
    return redirect(auth_url)


@app.route("/api/logout")
def logout():
    session['access_token'] = None
    session['refresh_token'] = None
    r = RedisHelper()
    r.access_token = None
    r.refresh_token = None
    r.sync(PROJECT_PATH)
    return redirect("/")


@app.route("/api/oauth/login")
def auth():

    state = request.args.get('state', '')
    code = request.args.get('code', '')

    access_token, refresh_token = oauth.authenticate(code)

    session['access_token'] = access_token
    session['refresh_token'] = refresh_token

    r = RedisHelper()
    r.access_token = access_token
    r.refresh_token = refresh_token
    r.sync(PROJECT_PATH)

    return redirect("/")


def get_vectors(box, folder_id, template_name):
    metafields = []
    for f in box.get_files(folder_id):
        m = box.get_file_metafield_or_none(f=f,
                                           template_name=template_name)
        if m:
            m['file_name'] = f.name
            metafields.append(m)
    return metafields


def get_columns(box, template_name):
    return Col(box.get_scope_templates_or_none(template_name)).prepare()


def create_json(path, data):
    with open(path, "w") as out:
        out.write(json.dumps(data))


@app.route("/api/schema/<template_name>/<folder_id>")
def schema(template_name, folder_id):

    with get_client(session) as client:
        box = BoxHelper(client)
        columns = get_columns(box, template_name)
        logging.info("got {} columns".format(len(columns)))
        return json.dumps({"result": "OK", "data": columns})
    return json.dumps({"result": "error", "error_msg": "", "data": {}})


@app.route("/api/vectors/<template_name>/<folder_id>")
def vectors(template_name, folder_id):
    import ipdb; ipdb.set_trace()
    with get_client(session) as client:
        box = BoxHelper(client)
        vectors = get_vectors(box, folder_id, template_name)
        logging.info("got {} vectors".format(len(vectors)))
        return json.dumps({"result": "OK", "data": vectors})
    return json.dumps({"result": "error", "error_msg": "", "data": {}})
