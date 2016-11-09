import os
import settings
# TODO (sao): write an async box helper

__all__ = ("BoxHelper", )


class BoxHelper:

    def __init__(self, client):
        self._client = client

    @property
    def client(self):
        return self._client

    # public methods #
    def get_folder(self, folder_id=None):
        if not folder_id:
            folder_id="0"
        folder = self._client.folder(folder_id).get()
        return folder

    def get_file(self, file_id):
        return self._client.file(file_id).get()

    def get_file_metafields(self, scope="enterprise", f=None, f_id=None):
        if not f and not f_id:
            raise Exception("no file_id or file object defined")
        f_id = f.id or f_id
        if f_id:
            url = self._client.get_url("files/{}/metadata/".format(f_id))
            response = self._client.make_request(method="GET", url=url)
            return response.json()

    def get_file_metafield_or_none(self, template_name, scope="enterprise", f=None, f_id=None):
        metafields = self.get_file_metafields(scope, f, f_id)

        metafields = metafields.get('entries')
        if not metafields:
            return None

        for metafield_set in metafields:
            if metafield_set.get("$template") == template_name:
                return metafield_set

    def get_metadata_template(self, template, scope="enterprise"):
        """
        /metadata_templates/SCOPE/TEMPLATE/schema
        """
        url = self._client.get_url("metadata_templates/{}/{}/schema".format(scope, template))
        response = self._client.make_request(method="GET", url=url)
        return response.json()

    def get_scope_templates_or_none(self, template_name=None):
        """
        self.client.make_request(method="GET",
                                 url=self.client.get_url("metadata_templates/enterprise")).json()
        """
        url = self._client.get_url("metadata_templates/enterprise")
        response = self._client.make_request(method="GET",
                                             url=url)
        if not template_name:
            return response.json()

        templates = response.json()
        for entry in templates.get("entries", []):
            if entry["templateKey"] == template_name:
                return entry

    def create_metadata(self, f_id, type, template):
        pass


    def create_metadata_file(self, file_id, template, template_meta, data, scope="enterprise"):
        """
        creates a metadata instance
        and attaches it to a file
        """

        template_to_key = {}
        for template_el in template_meta['fields']:
            template_to_key[template_el['displayName']] = template_el['key']

        values = []
        for line in data:
            v = {}
            f_id = line["Box link ID"]
            for k, val in line.items():
                if k in template_to_key and val:
                    v[template_to_key[k]] = val

            values.append((f_id, v))

        for f_id, els in values:
            metadata = self._client.file(f_id).metadata(scope, template)
            try:
                metadata.delete()
            except Exception as e: #TODO (sao): change to box exception
                print(e)

            try:
                metadata.create(els)
            except Exception as e: #TODO (sao): change to box exception
                print(e)

    def update_metadata(self, f_id, template, data, scope="enterprise"):
        """
        /files/FILE_ID/metadata/SCOPE/TEMPLATE
        op - string The operation type. Must be add, replace, remove , test, move, or copy.
        path - string The path that designates the key, in the format of a JSON-Pointer.
        Since all keys are located at the root of the metadata instance,
        the key must be prefixed with a /. Special characters ~ and / in the key must be
        escaped according to JSON-Pointer specification. The value at the path must exist
        for the operation to be successful.
        """
        raise NotImplementedError

    def get_files(self, f_id, offset=0, files=[], skipped=[]):

        folder = self.client.folder(f_id).get(fields=('id', 'name'))
        items = folder.get_items(limit=settings.LIMIT,
                                 offset=offset,
                                 fields=('id', 'name', 'type', "path_collection"))

        for f in items:
            if f.type == 'file':
                name, ext = os.path.splitext(f.name)
                #  if ext in settings.GOOD_FILE_EXTENSIONS:
                if f.id not in skipped:
                    files.append(f)
                    skipped.append(f.id)
            elif f.type == 'folder':
                fs = self.get_files(f.id,
                                    files=files,
                                    skipped=skipped)

        if len(items) >= settings.LIMIT:
            return self.get_files(f_id, offset + settings.LIMIT, files, skipped)
        else:
            return files
