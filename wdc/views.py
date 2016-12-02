#! coding: utf-8
# views.py

import os
import json

from wdc import app, oauth, get_client, RedisHelper, PROJECT_PATH, Col, insert_tokens_into_session
from box import BoxHelper

from flask import render_template, request, redirect, make_response, session, send_file

import logging

from settings import SERVICES, FILES_DIR

from urllib import quote


def return_json(data):
    return json.dumps({"result": "OK",
                       "status": 200,
                       "error_msg": "",
                       "data": data})

def return_error(error):
    return json.dumps({
        'result': 'error',
        'status': 500,
        'error_msg': str(error),
        'data': ""
    })

@app.route("/")
def index():
    # TODO: make class-based index with support of dynamic project naming
    if not session:
        insert_tokens_into_session(session)

    try:
        with get_client(session) as client:
           title = "BOXWIZARDS tableau WDC"
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

def get_folder_template(template_name, folder_id):

    r = RedisHelper()
    if "none" not in (template_name, folder_id):
        r.update(PROJECT_PATH, template=template_name, folder=folder_id)
    else:
        r.get(PROJECT_PATH)
    return r.template, r.folder


@app.route("/api/schema/<template_name>/<folder_id>")
def schema(template_name, folder_id):

    template_name, folder_id = get_folder_template(template_name, folder_id)

    with get_client(session) as client:
        box = BoxHelper(client)
        columns = get_columns(box, template_name)
        logging.info("got {} columns".format(len(columns)))
        return json.dumps({"result": "OK", "data": columns})
    return json.dumps({"result": "error", "error_msg": "", "data": {}})


@app.route("/api/vectors/<template_name>/<folder_id>")
def vectors(template_name, folder_id):

    template_name, folder_id = get_folder_template(template_name, folder_id)

    with get_client(session) as client:
        box = BoxHelper(client)
        vectors = get_vectors(box, folder_id, template_name)
        logging.info("got {} vectors".format(len(vectors)))
        return json.dumps({"result": "OK", "data": vectors})
    return json.dumps({"result": "error", "error_msg": "", "data": {}})


@app.route('/api/set_folder/<folder>')
def set_folder(folder):
    r = RedisHelper()
    r.update(PROJECT_PATH, folder=folder)
    return json.dumps({"result": "OK"})

@app.route('/api/set_template/<template>')
def set_template(template):
    r = RedisHelper()
    r.update(PROJECT_PATH, template=template)
    return json.dumps({"result": "OK"})

import requests
@app.route('/api/process/<template_name>/<folder_id>', methods=("GET",))
def process(template_name, folder_id):

    template_name, folder_id = get_folder_template(template_name, folder_id)
    service = SERVICES['nltk']
    url = "http://" + service['host'] + ":%d" % service['port'] + "/services/keywords/pattern"
    data = requests.get(url).content
    return return_json(data)


def __simplify_templates(templates):
    result = {}
    for template in templates['entries']:
        result[template['templateKey']] = {
            'displayName': template['displayName'],
            "fields": [(item['key'], item['displayName']) for item in template['fields']]
        }
        return result


def __simplify_metadata(metadata):
    result = {}
    for entry in metadata['entries']:
        result[entry["$template"]] = entry
    return result


def __parse_files(box, files):
    _files = []
    for file_ in files:
        file_id = file_.id
        if not file_id:
            pass
        _files.append({
            "name": file_.name,
             "id": file_id,
             "path": os.path.join(*[p['name'] for p in file_.path_collection['entries']]),
             "metafields": __simplify_metadata(box.get_file_metafields(f_id=file_id))
        })
    return _files

@app.route('/api/export/<template_name>/<folder_id>', methods=("GET",))
def export(template_name, folder_id):

    template_name, folder_id = get_folder_template(template_name, folder_id)

    if not folder_id:
        return None

    body = {}
    with get_client(session) as client:
        box = BoxHelper(client)
        files = box.get_files(f_id=folder_id)
        body['files'] = __parse_files(box, files)
        body['templates'] = __simplify_templates(box.get_scope_templates_or_none())

    service = SERVICES['excel']

    url = "http://" + service['host'] + ":%s" % service['port'] + '/services/excel/download'
    data = requests.post(url, data=json.dumps(body)).content

    with open(os.path.join(FILES_DIR, 'test.xlsx'), 'w') as out:
        out.write(data)
    return return_json("/" + os.path.join('static', 'files', 'test.xlsx'))

    # excel_header = 'application/vnd.openxmlformats-officedocument.spreadsheet.sheet'
    # return send_file(data) #, attachment_filename="test.xlsx", mimetype=excel_header)
    #return render_template("processed.html", rows=data)


def __upload_metadata(data):
    with get_client(session) as client:
        box = BoxHelper(client)
        templates = box.get_scope_templates_as_dict()
        for row in data:
            template, vectors = row['template'], row['vector']
            try:
                box.create_metadata(template, templates[template], vectors)
            except Exception as e:
                logging.exception(e)
    return data

@app.route('/api/import/<folder_id>', methods=("POST",))
def import_xlsx(folder_id):

    if not folder_id:
        return return_error('error')

    try:
        f = request.files['file']
        file_data = f.read()

        service = SERVICES['excel']
        url = "http://" + service['host'] + ":%s" % service['port'] + '/services/excel/parse'
        data = requests.post(url, files={'file': file_data}).content

        if data:
            data = json.loads(data)
            data = data['data']
            data = __upload_metadata(data)

    except Exception as e:
        return return_error(e)

    return return_json("data")

