#! coding: utf-8
# runserver.py
from wdc import app

if __name__ == "__main__":
    app.run("localhost", 5000, debug=True)

