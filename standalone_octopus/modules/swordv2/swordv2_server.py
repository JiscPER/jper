from flask import Blueprint, Response, request, url_for, make_response, abort, redirect, send_file

from functools import wraps

from standalone_octopus.core import app
from standalone_octopus.lib.webapp import ssl_required
from standalone_octopus.lib.negotiator import ContentNegotiator

from sss.spec import Errors, HttpHeaders, ValidationException
from sss.core import Auth, SwordError, AuthException, DepositRequest, DeleteRequest

# create the global configuration and import the implementation classes
from sss.config import Configuration
# ##config = Configuration(config_file=app.config.get("SWORDV2_SERVER_CONFIG"))
# ## 2016-08-25 TD : take the default (i.e. built-in) by implicitly setting config_file=None
# config = Configuration() # default configuration
# 2016-10-25 TD : make the original Configuration api work again.  The trick here was the
#                 observation that in 'local.cfg' the config varible /is/ already a dict!
config = Configuration(config_obj=app.config.get("SWORDV2_SERVER_CONFIG"))
Authenticator = config.get_authenticator_implementation()
SwordServer = config.get_server_implementation()

blueprint = Blueprint('swordv2_server', __name__)


#################################################
## Error handling

def raise_error(sword_error, additional_headers=None):
    body = sword_error.error_document if not sword_error.empty else ""
    resp = make_response(body)
    resp.mimetype = "text/xml"
    resp.status_code = sword_error.status
    if additional_headers is not None:
        for k, v in additional_headers.items():
            resp.headers[k] = v
    return resp

##################################################
## Authentication methods

def check_auth(username, password, obo=None):
    authenticator = Authenticator(config)
    auth = None
    try:
        auth = authenticator.basic_authenticate(username, password, obo)
    except AuthException as e:
        if e.authentication_failed:
            raise SwordError(status=401, empty=True)
        elif e.target_owner_unknown:
            raise SwordError(error_uri=Errors.target_owner_unknown, msg="unknown user " + str(obo) + " as on behalf of user", author="JPER")

    return auth

def basic_auth():
    auth = request.authorization
    if not auth:
        raise SwordError(status=401, empty=True)
    authobj = check_auth(auth.username, auth.password)
    if authobj is None:
        raise SwordError(status=401, empty=True)
    return authobj

###################################################
# Data extraction functions

def get_deposit(auth):
    d = DepositRequest()

    mapped_headers = request.headers

    h = HttpHeaders()
    d.set_from_headers(h.get_sword_headers(mapped_headers))

    if d.content_length > config.max_upload_size:
        raise SwordError(error_uri=Errors.max_upload_size_exceeded,
                        msg="Max upload size is " + str(config.max_upload_size) +
                        "; incoming content length was " + str(d.content_length),
                        author="JPER")

    # get the body as a stream (which should be available as the mimetype
    # is not handled by default by Flask, we hope!)
    d.content_file = request.stream

    # set the filename
    d.filename = h.extract_filename(mapped_headers)

    # now just attach the authentication data and return
    d.auth = auth
    return d

###################################################
## Protocol operations

@blueprint.route('/service-document', methods=['GET'])
@ssl_required
def service_document():
    """
    GET the service document - returns an XML document
    - sub_path - the path provided for the sub-service document
    """
    try:
        auth = basic_auth()
    except SwordError as e:
        return raise_error(e, {'WWW-Authenticate': 'Basic realm="JPER"'})

    # if we get here authentication was successful and we carry on (we don't care who authenticated)
    ss = SwordServer(config, auth)
    sd = ss.service_document()

    resp = make_response(sd)
    resp.mimetype = "application/atomsvc+xml"
    return resp

@blueprint.route("/collection/<collection_id>", methods=["POST"])
@ssl_required
def collection(collection_id):
    """
    POST either an Atom Multipart request, or a simple package into the specified collection
    Args:
    - collection_id:   The ID of the collection as specified in the requested URL
    Returns a Deposit Receipt
    """

    try:
        # authenticate
        auth = basic_auth()

        # FIXME: this is not a full implementation yet, so probably we won't do this until later
        # check the validity of the request
        # self.validate_deposit_request(web, "6.3.3", "6.3.1", "6.3.2")

        # take the HTTP request and extract a Deposit object from it
        deposit = get_deposit(auth)

        # go ahead and process the deposit.  Anything other than a success
        # will be raised as a sword error
        ss = SwordServer(config, auth)
        result = ss.deposit_new(collection_id, deposit)

        # created
        body = ""
        if config.return_deposit_receipt and result.receipt is not None:
            body = result.receipt

        resp = make_response(body)
        if body != "":
            resp.mimetype = "application/atom+xml;type=entry"

        if result.location is not None:
            resp.headers["Location"] = result.location

        if result.created:
            resp.status_code = 201
        elif result.accepted:
            resp.status_code = 202

        return resp

    except SwordError as e:
        return raise_error(e)

@blueprint.route("/entry/<path:entry_id>", methods=["GET"])
@ssl_required
def entry(entry_id):
    """
    GET a representation of the container in the appropriate (content negotiated) format as identified by
    the supplied id
    Args:
    - entry_id:   The ID of the container as supplied in the request URL
    Returns a representation of the container: SSS will return either the Atom Entry identical to the one supplied
    as a deposit receipt or the pure RDF/XML Statement depending on the Accept header
    """
    # authenticate
    try:
        auth = basic_auth()
        ss = SwordServer(config, auth)

        # first thing we need to do is check that there is an object to return, because otherwise we may throw a
        # 415 Unsupported Media Type without looking first to see if there is even any media to content negotiate for
        # which would be weird from a client perspective
        if not ss.container_exists(entry_id):
            abort(404)

        # get the content negotiation headers
        accept_header = request.headers.get("Accept")
        accept_packaging_header = request.headers.get("Accept-Packaging")

        # do the negotiation
        default_accept_parameters, acceptable = config.get_container_formats()
        cn = ContentNegotiator(default_accept_parameters, acceptable)
        accept_parameters = cn.negotiate(accept=accept_header)
        app.logger.info("Container requested in format: " + str(accept_parameters))

        # did we successfully negotiate a content type?
        if accept_parameters is None:
            raise SwordError(error_uri=Errors.content, status=415, empty=True)

        # now actually get hold of the representation of the container and send it to the client
        cont = ss.get_container(entry_id, accept_parameters)

        resp = make_response(cont)
        if cont is not None:
            resp.mimetype = accept_parameters.content_type.mimetype()

        return resp

    except SwordError as e:
        return raise_error(e)

@blueprint.route("/entry/<path:entry_id>/content", methods=["GET"])
@ssl_required
def content(entry_id):
    """
    GET the media resource content in the requested format (web request will include content negotiation via
    Accept header)
    Args:
    - entry_id:   the ID of the object in the store
    Returns the content in the requested format
    """

    auth = basic_auth()
    ss = SwordServer(config, auth)

    # first thing we need to do is check that there is an object to return, because otherwise we may throw a
    # 406 Not Acceptable without looking first to see if there is even any media to content negotiate for
    # which would be weird from a client perspective
    if not ss.media_resource_exists(entry_id):
        abort(404)

    # get the content negotiation headers
    accept_header = request.headers.get("Accept")
    accept_packaging_header = request.headers.get("Accept-Packaging")

    # do the negotiation
    default_accept_parameters, acceptable = config.get_media_resource_formats()
    cn = ContentNegotiator(default_accept_parameters, acceptable)
    accept_parameters = cn.negotiate(accept=accept_header, accept_packaging=accept_packaging_header)

    try:
        # can get hold of the media resource
        media_resource = ss.get_media_resource(entry_id, accept_parameters)
    except SwordError as e:
        return raise_error(e)

    # either send the client a redirect, or stream the content out
    if media_resource.redirect:
        return redirect(media_resource.url)
    else:
        resp = send_file(media_resource.filepath, mimetype=media_resource.content_type)
        resp.headers["Packaging"] = media_resource.packaging
        return resp

@blueprint.route("/entry/<path:entry_id>/statement/<type>", methods=["GET"])
@ssl_required
def statement(entry_id, type):
    try:
        # authenticate
        auth = basic_auth()
        ss = SwordServer(config, auth)

        # first thing we need to do is check that there is an object to return, because otherwise we may throw a
        # 415 Unsupported Media Type without looking first to see if there is even any media to content negotiate for
        # which would be weird from a client perspective
        if not ss.container_exists(entry_id):
            abort(404)

        if type == "atom":
            type = "application/atom+xml;type=feed"
        elif type == "rdf":
            type = "application/rdf+xml"
        else:
            type = "application/atom+xml;type=feed"

        # now actually get hold of the representation of the statement and send it to the client
        cont = ss.get_statement(entry_id, type)

        resp = make_response(cont)
        resp.mimetype = type
        return resp

    except SwordError as e:
        return raise_error(e)
