from flask import Blueprint, make_response, url_for, request, abort
import json
from octopus.lib.dataobj import ObjectSchemaValidationError
from octopus.core import app
from octopus.lib import webapp
from octopus.modules.crud.factory import CRUDFactory

blueprint = Blueprint('webapi', __name__)

def _not_found():
    app.logger.debug("Sending 404 Not Found")
    resp = make_response(json.dumps({"status" : "not found"}))
    resp.mimetype = "application/json"
    resp.status_code = 404
    return resp

def _bad_request(e):
    app.logger.info("Sending 400 Bad Request from client: {x}".format(x=e.message))
    resp = make_response(json.dumps({"status" : "error", "error" : e.message}))
    resp.mimetype = "application/json"
    resp.status_code = 400
    return resp

def _created(obj, container_type):
    app.logger.info("Sending 201 Created: {x} {y}".format(x=container_type, y=obj.id))
    url = url_for("crud.entity", container_type=container_type, type_id=obj.id)
    resp = make_response(json.dumps({"status" : "success", "id" : obj.id, "location" : url }))
    resp.mimetype = "application/json"
    resp.headers["Location"] = url
    resp.status_code = 201
    return resp

def _success():
    app.logger.debug("Sending 200 OK")
    resp = make_response(json.dumps({"status" : "success"}))
    return resp

@blueprint.route("/validate", methods=["POST"])
@webapp.jsonp
def validate():
    pass

@blueprint.route("/notification", methods=["POST"])
@webapp.jsonp
def create_notification():
    pass

@blueprint.route("/notification/<notification_id>", methods=["GET"])
@webapp.jsonp
def retrieve_notification(notification_id):
    pass

@blueprint.route("/notification/<notification_id>/content", methods=["GET"])
@webapp.jsonp
def retrieve_content(notification_id):
    pass

@blueprint.route("/notification/<notification_id>/content/<content_id>", methods=["GET"])
@webapp.jsonp
def proxy_content(notification_id, content_id):
    pass

@blueprint.route("/routed", methods=["GET"])
@webapp.jsonp
def list_all_routed():
    pass

@blueprint.route("/routed/<repo_id>", methods=["GET"])
@webapp.jsonp
def list_repository_routed(repo_id):
    pass