from flask import Blueprint, make_response, url_for, request, abort
import json
from octopus.core import app
from octopus.lib import webapp
from flask.ext.login import login_user, logout_user, current_user, login_required
from service.api import JPER, ValidationException

blueprint = Blueprint('webapi', __name__)

def _not_found():
    app.logger.debug("Sending 404 Not Found")
    resp = make_response(json.dumps({"status" : "not found"}))
    resp.mimetype = "application/json"
    resp.status_code = 404
    return resp

def _bad_request(message):
    app.logger.info("Sending 400 Bad Request from client: {x}".format(x=message))
    resp = make_response(json.dumps({"status" : "error", "error" : message}))
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

@blueprint.before_request
def authenticate():
    # this is where we should inspect the api key, and login the user
    # FIXME: maybe belongs in the account module
    pass

@blueprint.route("/validate", methods=["POST"])
@webapp.jsonp
def validate():
    md = None
    zipfile = None

    if len(request.files) > 0:
        # this is a multipart request, so extract the data accordingly
        metadata = request.files["metadata"]
        content = request.files["content"]

        # now, do some basic validation on the incoming http request (not validating the content,
        # that's for the underlying validation API to do
        if metadata.mimetype != "application/json":
            return _bad_request("Content-Type for metadata part of multipart request must be application/json")

        rawmd = metadata.stream.read()
        try:
            md = json.loads(rawmd)
        except:
            return _bad_request("Unable to parse metadata part of multipart request as valid json")

        if content.mimetype != "application/zip":
            return _bad_request("Content-Type for content part of multipart request must be application/zip")

        zipfile = content.stream
    else:
        if "content-type" not in request.headers or request.headers["content-type"] != "application/json":
            return _bad_request("Content-Type must be application/json")

        try:
            md = json.loads(request.data)
        except:
            return _bad_request("Unable to parse request body as valid json")

    try:
        JPER.validate(current_user, md, zipfile)
    except ValidationException as e:
        return _bad_request(e.message)

    return '', 204

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