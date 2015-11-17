"""
Blueprint which provides the RESTful web API for JPER
"""
from flask import Blueprint, make_response, url_for, request, abort, redirect, current_app
from flask import stream_with_context, Response
import json, csv
from octopus.core import app
from octopus.lib import webapp, dates
from flask.ext.login import login_user, logout_user, current_user, login_required
from service.api import JPER, ValidationException, ParameterException
from service import models

blueprint = Blueprint('webapi', __name__)

def _not_found():
    """
    Construct a response object to represent a 404 (Not Found)

    :return: Flask response for a 404, with an empty response body
    """
    app.logger.debug("Sending 404 Not Found")
    resp = make_response("")
    resp.mimetype = "application/json"
    resp.status_code = 404
    return resp

def _bad_request(message):
    """
    Construct a response object to represent a 400 (Bad Request) around the supplied message

    :return: Flask response for a 400 with a json response body containing the error
    """
    app.logger.info("Sending 400 Bad Request from client: {x}".format(x=message))
    resp = make_response(json.dumps({"status" : "error", "error" : message}))
    resp.mimetype = "application/json"
    resp.status_code = 400
    return resp

def _accepted(obj):
    """
    Construct a response object to represent a 202 (Accepted) for the supplied object

    :param obj: the object that was accepted
    :return: Flask response for a 202 with the id of the object in the json body, and the Location header set correctly
    """
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
def standard_authentication():
    """Check remote_user on a per-request basis."""
    remote_user = request.headers.get('REMOTE_USER', '')
    #tp, apik = request.headers.get('Authorization', '').lower().split(None, 1)
    apik = False
    if not apik:
        try:
            apik = request.values.get('API_KEY', request.values.get('api_key', False))
        except:
            try:
                apik = request.json.get('API_KEY', request.json.get('api_key', False))    
            except:
                pass

    if remote_user:
        print "remote user present " + remote_user
        app.logger.info("Remote user connecting: {x}".format(x=remote_user))
        user = models.Account.pull(remote_user)
        if user:
            login_user(user, remember=False)
        else:
            abort(401)
    elif apik:
        print "API key provided " + apik
        app.logger.info("API key connecting: {x}".format(x=apik))
        res = models.Account.query(q='api_key:"' + apik + '"')['hits']['hits']
        if len(res) == 1:
            user = models.Account.pull(res[0]['_source']['id'])
            if user is not None:
                login_user(user, remember=False)
            else:
                abort(401)
        else:
            abort(401)
    else:
        print "aborting, no user"
        app.logger.info("Standard authentication failed")
        abort(401)

class BadRequest(Exception):
    """
    Generic Exception for a bad request
    """
    pass

def _get_parts():
    """
    Used to extract metadata and content from an incoming request

    :return: a tuple containing the metadata parsed out of the incoming json, and a file-handle (read-once) for the binary content
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
    """
    Receive a POST to the /validate endpoint and process it

    :return: A 400 (Bad Request) if not valid, or a 204 if successful
    """
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
    """
    Receive a POST to the /notification endpoint to create a notification, and process it

    :return: A 400 (Bad Request) if not valid, or a 202 (Accepted) if successful
    """
    try:
        md, zipfile = _get_parts()
    except BadRequest as e:
        return _bad_request(e.message)

    try:
        notification = JPER.create_notification(current_user, md, zipfile)
        if not notification:
            abort(401)
    except ValidationException as e:
        return _bad_request(e.message)

    return _accepted(notification)

@blueprint.route("/notification/<notification_id>", methods=["GET"])
@webapp.jsonp
def retrieve_notification(notification_id):
    """
    Receive a GET on a specific notification, as identified by the notification id, and return the body
    of the notification

    :param notification_id: the id of the notification to retrieve
    :return: 404 (Not Found) if not found, else 200 (OK) and the outgoing notification as a json body
    """
    notification = JPER.get_notification(current_user, notification_id)
    if notification is None:
        return _not_found()
    resp = make_response(notification.json())
    resp.mimetype = "application/json"
    resp.status_code = 200
    return resp

@blueprint.route("/notification/<notification_id>/content", methods=["GET"])
@blueprint.route("/notification/<notification_id>/content/<filename>", methods=["GET"])
@webapp.jsonp
def retrieve_content(notification_id, filename=None):
    """
    Receive a GET against the default content or a specific content file in a notification and supply the binary
    in return

    :param notification_id: the notification whose content to retrieve
    :param filename: the filename of the content file in the notification
    :return: 404 (Not Found) if either the notification or content are not found) or 200 (OK) and the binary content
    """
    app.logger.info("{x} {y} content requested".format(x=notification_id, y=filename))
    try:
        filestream = JPER.get_content(current_user, notification_id, filename)
        return Response(stream_with_context(filestream))
    except:
        return _not_found()

@blueprint.route("/notification/<notification_id>/proxy/<pid>", methods=["GET"])
def proxy_content(notification_id, pid):
    app.logger.info("{x} {y} proxy requested".format(x=notification_id, y=pid))
    purl = JPER.get_proxy_url(current_user, notification_id, pid)
    if purl is not None:
        return redirect(purl)
    else:
        return _not_found()

def _list_request(repo_id=None):
    """
    Process a list request, either against the full dataset or the specific repo_id supplied

    This function will pull the arguments it requires out of the Flask request object.  See the API documentation
    for the parameters of these kinds of requests.

    :param repo_id: the repo id to limit the request to
    :return: Flask response containing the list of notifications that are appropriate to the parameters
    """
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
    """
    List all the notifications that have been routed to any repository, limited by the parameters supplied
    in the URL.

    See the API documentation for more details.

    :return: a list of notifications appropriate to the parameters
    """
    return _list_request()

@blueprint.route("/routed/<repo_id>", methods=["GET"])
@webapp.jsonp
def list_repository_routed(repo_id):
    """
    List all the notifications that have been routed to the specified repository, limited by the parameters supplied
    in the URL.

    See the API documentation for more details.

    :param repo_id: the id of the reponsitory whose notifications to retrieve
    :return: a list of notifications appropriate to the parameters
    """
    return _list_request(repo_id)

@blueprint.route("/config", methods=["GET","POST"])
@blueprint.route("/config/<repoid>", methods=["GET","POST"])
@webapp.jsonp
def config(repoid=None):
    app.logger.info(current_user.id + " " + request.method + " to config route")
    if repoid is None:
        if current_user.has_role('repository'):
            repoid = current_user.id
        elif current_user.has_role('admin'):
            return '' # the admin cannot do anything at /config, but gets a 200 so it is clear they are allowed
        else:
            abort(400)
    elif not current_user.has_role('admin'): # only the superuser can set a repo id directly
        abort(401)
    rec = models.RepositoryConfig().pull_by_repo(repoid)
    if rec is None:
        rec = models.RepositoryConfig()
        rec.repository = repoid
    if request.method == 'GET':
        # get the config for the current user and return it
        # this route may not actually be needed, but is convenient during development
        # also it should be more than just the strings data once complex configs are accepted
        resp = make_response(json.dumps(rec.data))
        resp.mimetype = "application/json"
        return resp
    elif request.method == 'POST':
        if request.json:
            saved = rec.set_repo_config(jsoncontent=request.json,repository=repoid)
        else:
            try:
                if request.files['file'].filename.endswith('.csv'):
                    saved = rec.set_repo_config(csvfile=request.files['file'],repository=repoid)
                elif request.files['file'].filename.endswith('.txt'):
                    saved = rec.set_repo_config(textfile=request.files['file'],repository=repoid)
            except:
                saved = False
        if saved:
            return ''
        else:
            abort(400)

            
            
            
            