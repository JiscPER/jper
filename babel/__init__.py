from flask import Flask
from flask.ext.babel import Babel

app = Flask(__name__)
app.config.from_pyfile('babel.cfg')
babel = Babel(app)