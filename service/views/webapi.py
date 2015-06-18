from flask import Blueprint, make_response, url_for, request, abort, redirect
import json
from octopus.core import app
from octopus.lib import webapp, dates
from flask.ext.login import login_user, logout_user, current_user, login_required
from service.api import JPER, ValidationException, ParameterException

blueprint = Blueprint('webapi', __name__)

def _not_found():
    app.logger.debug("Sending 404 Not Found")
    resp = make_response("")
    resp.mimetype = "application/json"
    resp.status_code = 404
    return resp

def _bad_request(message):
    app.logger.info("Sending 400 Bad Request from client: {x}".format(x=message))
    resp = make_response(json.dumps({"status" : "error", "error" : message}))
    resp.mimetype = "application/json"
    resp.status_code = 400
    return resp

"""
Not currently used, but kept around in case we want them later
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
"""

def _accepted(obj):
    app.logger.info("Sending 202 Accepted: {x}".format(x=obj.id))
    root = request.url_root
    if root.endswith("/"):
        root = root[:-1]
    url = root + url_for("webapi.retrieve_notification", notification_id=obj.id)
    resp = make_response(json.dumps({"status" : "accepted", "id" : obj.id, "location" : url }))
    resp.mimetype = "application/json"
    resp.headers["Location"] = url
    resp.status_code = 202
    return resp

@blueprint.before_request
def authenticate():
    # this is where we should inspect the api key, and login the user
    # FIXME: maybe belongs in the account module
    pass

class BadRequest(Exception):
    pass

def _get_parts():
    """
    Used to extract metadata and content from an incoming request
    :return:
    """
    md = None
    zipfile = None

    if len(request.files) > 0:
        # this is a multipart request, so extract the data accordingly
        metadata = request.files["metadata"]
        content = request.files["content"]

        # now, do some basic validation on the incoming http request (not validating the content,
        # that's for the underlying validation API to do
        if metadata.mimetype != "application/json":
            raise BadRequest("Content-Type for metadata part of multipart request must be application/json")

        rawmd = metadata.stream.read()
        try:
            md = json.loads(rawmd)
        except:
            raise BadRequest("Unable to parse metadata part of multipart request as valid json")

        if content.mimetype != "application/zip":
            raise BadRequest("Content-Type for content part of multipart request must be application/zip")

        zipfile = content.stream
    else:
        if "content-type" not in request.headers or request.headers["content-type"] != "application/json":
            raise BadRequest("Content-Type must be application/json")

        try:
            md = json.loads(request.data)
        except:
            raise BadRequest("Unable to parse request body as valid json")

    return md, zipfile

@blueprint.route("/validate", methods=["POST"])
@webapp.jsonp
def validate():
    try:
        md, zipfile = _get_parts()
    except BadRequest as e:
        return _bad_request(e.message)

    try:
        JPER.validate(current_user, md, zipfile)
    except ValidationException as e:
        return _bad_request(e.message)

    return '', 204

@blueprint.route("/notification", methods=["POST"])
@webapp.jsonp
def create_notification():
    try:
        md, zipfile = _get_parts()
    except BadRequest as e:
        return _bad_request(e.message)

    try:
        notification = JPER.create_notification(current_user, md, zipfile)
    except ValidationException as e:
        return _bad_request(e.message)

    return _accepted(notification)

@blueprint.route("/notification/<notification_id>", methods=["GET"])
@webapp.jsonp
def retrieve_notification(notification_id):
    notification = JPER.get_notification(current_user, notification_id)
    if notification is None:
        return _not_found()
    resp = make_response(notification.json())
    resp.mimetype = "application/json"
    resp.status_code = 200
    return resp

@blueprint.route("/notification/<notification_id>/content", methods=["GET"])
@webapp.jsonp
def retrieve_content(notification_id):
    store_url = JPER.get_store_url(current_user, notification_id)
    if store_url is None:
        return _not_found()
    JPER.record_retrieval(current_user, notification_id)
    return redirect(store_url, 303)

@blueprint.route("/notification/<notification_id>/content/<content_id>", methods=["GET"])
@webapp.jsonp
def proxy_content(notification_id, content_id):
    public_url = JPER.get_public_url(current_user, notification_id, content_id)
    if public_url is None:
        return _not_found()
    JPER.record_retrieval(current_user, notification_id, content_id)
    return redirect(public_url, 303)

def _list_request(repo_id=None):
    since = request.values.get("since")
    page = request.values.get("page", app.config.get("DEFAULT_LIST_PAGE_START", 1))
    page_size = request.values.get("pageSize", app.config.get("DEFAULT_LIST_PAGE_SIZE", 25))

    if since is None or since == "":
        return _bad_request("Missing required parameter 'since'")

    try:
        since = dates.reformat(since)
    except ValueError as e:
        return _bad_request("Unable to understand since date '{x}'".format(x=since))

    try:
        page = int(page)
    except:
        return _bad_request("'page' parameter is not an integer")

    try:
        page_size = int(page_size)
    except:
        return _bad_request("'pageSize' parameter is not an integer")

    try:
        nlist = JPER.list_notifications(current_user, since, page=page, page_size=page_size, repository_id=repo_id)
    except ParameterException as e:
        return _bad_request(e.message)

    resp = make_response(nlist.json())
    resp.mimetype = "application/json"
    resp.status_code = 200
    return resp

@blueprint.route("/routed", methods=["GET"])
@webapp.jsonp
def list_all_routed():
    return _list_request()

@blueprint.route("/routed/<repo_id>", methods=["GET"])
@webapp.jsonp
def list_repository_routed(repo_id):
    return _list_request(repo_id)