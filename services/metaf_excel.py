# metaf_excel.py
import json
import logging

from flask import Flask

from flask import request, make_response, send_file

from werkzeug.exceptions import MethodNotAllowed

import xlwt, xlrd
from xlwt import Font, Borders, XFStyle

from io import BytesIO

from settings import SERVICES

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s:%(name)s %(levelname)s:%(message)s")
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

app = Flask(__name__)


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


class ExcelReader(object):
    def __init__(self, bytestream, **kwargs):
        self.bytestream = bytestream

        self._offset = kwargs.get("col_offset", 0)
        self._header_row_num = kwargs.get("col_header_num", 0)
        self._values_row_start = kwargs.get("values_row_start", 1)

        self.wb = xlrd.open_workbook(file_contents=self.bytestream)

    def get_row_values(self, row):
        def make_value(val):
            return val if val != "*N/A*" else None
        return [make_value(x.value) for x in row]

    def read_sheet(self, sheet):
        result = []
        headers = self.get_row_values(sheet.row(self._header_row_num))[self._offset:]
        for pos in xrange(sheet.nrows):
            if pos < self._values_row_start:
                continue
            values = self.get_row_values(sheet.row(pos))[self._offset:]
            res = {}
            for index, val in enumerate(values):
                if val != "n/a":
                    res[headers[index]] = val
            result.append(res)
        return result

    def read(self):
        result = []
        for sheet in self.wb.sheets():
            if sheet.name.lower() != 'all files':
                row = {
                    'template': sheet.name,
                    'vector': self.read_sheet(sheet)
                }
                result.append(row)
        return result


class ExcelWriter(object):
    def __init__(self, path=None, is_byte=True):
        self.path = path
        self._is_byte = is_byte

        self._style_header = XFStyle()
        self._style_offset = XFStyle()

        borders = Borders()
        borders.left = 1
        borders.right = 1
        borders.top = 1
        borders.bottom = 1

        font = Font()
        font.name = "Arial"
        font.height = 15 * 15
        font.bold = True

        self._style_header.borders = borders
        self._style_header.font = font

        self._style_text = xlwt.easyxf('font: name Times New Roman, color-index black, bold on')

        self.workbook = xlwt.Workbook(encoding="cp1251")

    def write_line(self, sheet, x, y, style, line):
        for el in line:
            sheet.write(x, y, el, style)
            y += 1

    def write_sheet(self, template_name, template_fields, files):
        sheet = self.workbook.add_sheet(template_name, cell_overwrite_ok=True)
        base_headers = ["id", "path", "name"]
        add_headers = [tf for tf, dn in template_fields]
        headers = base_headers + add_headers

        x, y = 0, 0
        self.write_line(sheet, x, y, self._style_header, headers)
        x = 1
        for f in files:
            if template_name in f['metafields']:  # base case
                line = [f.get(h) for h in base_headers]
                line.extend([f['metafields'][template_name].get(h, "n/a") for h in add_headers])
                self.write_line(sheet, x, 0, self._style_text, line)
                x += 1
            elif not add_headers: # for sheet "all files"
                line = [f.get(h) for h in base_headers]
                self.write_line(sheet, x, 0, self._style_text, line)
                x += 1

    def write(self, templates, files):
        for template_name, template_fields in templates.items():
            self.write_sheet(template_name, template_fields['fields'], files)
        self.write_sheet("all files", [], files)

        bytestream = BytesIO()
        self.workbook.save(bytestream)
        bytestream.seek(0)
        return bytestream

@app.route("/services/excel/download", methods=("POST",))
def create_excel_file():
    """
    gets the file list and metadata from the input and
    creates an excel file to download it

    body: file: (name, path, )
    """
    if request.method != "POST":
        raise MethodNotAllowed

    logging.info("Start creating an excel file")

    data = json.loads(request.data)

    templates = data.get('templates')
    files = data.get('files')

    writer = ExcelWriter(is_byte=True)
    bytestream = writer.write(templates, files)

    excel_header = 'application/vnd.openxmlformats-officedocument.spreadsheet.sheet'
    excel_header = "application/vnd.ms-excel"
    logging.info('Returns excel file')
    # TODO: change file name
    return send_file(bytestream,
                     mimetype=excel_header)


@app.route("/services/excel/parse", methods=("POST",))
def create_metafields_from_file():
    """
    reads the file,
    grabs data from the file and
    makes creates templates versus each file
    if the excel spreadsheet
    """
    logging.info("Start uploading an excel file")

    fi = request.files.get('file')
    if not fi:
        return return_error("ERROR: Empty file received")
    file_data = fi.read()

    reader = ExcelReader(file_data)
    data = reader.read()

    if data:
        return return_json(data)
    return return_error("ERROR: Empty data from file")




if __name__ == "__main__":
    service = SERVICES['excel']
    app.run(service['host'], service['port'], debug=True)



