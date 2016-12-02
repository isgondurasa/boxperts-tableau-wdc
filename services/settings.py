import os

from os.path import abspath, dirname

CLIENT_ID = "8m71okna5xhftdx6sv7yd6un3ophi1du"
CLIENT_SECRET = "n6xVsfwuKQf7lMhnvW0QQC95tW7TJuT0"

BOXWIZARDS_PATH = "../metafields/"

SECRET_KEY = "ulK2ds3lMi42-jKsdl2Ff-0gb5N2nSb!4n/ds76?-snJb38="
LIMIT = 20
GOOD_FILE_EXTENSIONS = ["doc", "docx", "txt", "png", "pdf", "xls", "xlsx"]

PROJECT_ROOT = abspath(dirname(__file__))

REDIS_HOST = os.environ.get("REDIS_HOST", "192.168.99.100")
REDIS_PORT = 6379

INDEX = "test"

SERVICES = {
    "excel": dict(host=os.environ.get('EXCEL_HOST', "localhost"),
                  port=os.environ.get('EXCEL_PORT', 5001)),
    "nltk": dict(host=os.environ.get('NLTK_HOST', 'localhost'),
                 port=os.environ.get('NLTK_PORT', 5002))
}
