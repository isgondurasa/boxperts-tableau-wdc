#! coding: utf-8
# runserver.py
from wdc import app

if __name__ == "__main__":
    app.run("0.0.0.0", 5000, debug=True)

