from flask import Flask
from flask import redirect, render_template

from DatabaseAccess import DatabaseAccess

app = Flask(__name__)
db = DatabaseAccess("images")

from views import *

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8996, debug=False,threaded=True)
