from flask import Blueprint, request, make_response
from standalone_octopus.core import app
from standalone_octopus.lib import webapp, plugin
import json

blueprint = Blueprint('rolling', __name__)

@blueprint.route('/publish', methods=['POST'])
@webapp.jsonp
def publish():
    types = request.json.get("types", [])
    map = app.config.get("ESDAO_ROLLING_PLUGINS", {})
    for t in types:
        klazz = plugin.load_class(map.get(t))
        klazz.publish()
    return ""

@blueprint.route('/rollback', methods=['POST'])
@webapp.jsonp
def rollback():
    types = request.json.get("types", [])
    map = app.config.get("ESDAO_ROLLING_PLUGINS", {})
    for t in types:
        klazz = plugin.load_class(map.get(t))
        klazz.rollback()
    return ""

@blueprint.route("/status", methods=["GET"])
@webapp.jsonp
def status():
    map = app.config.get("ESDAO_ROLLING_PLUGINS", {})
    resp = {}
    for k,v in map.items():
        klazz = plugin.load_class(v)
        s = klazz.rolling_status()
        resp[k] = s
    r = make_response(json.dumps(resp))
    r.mimetype = "application/json"
    return r

@blueprint.route("/refresh", methods=["GET"])
def refresh():
    map = app.config.get("ESDAO_ROLLING_PLUGINS", {})
    for k, v in map.items():
        klazz = plugin.load_class(v)
        klazz.rolling_refresh()
    return ""