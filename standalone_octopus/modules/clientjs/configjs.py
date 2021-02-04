from flask import Blueprint, make_response, render_template

from standalone_octopus.core import app

blueprint = Blueprint('configjs', __name__)

# this allows us to serve our standard javascript config
@blueprint.route("/javascript/config.js")
def javascript_config():
    configs = {}
    for key, val in app.config.items():
        if key.startswith("CLIENTJS_"):
            nk = key[9:].lower()
            configs[nk] = val
    resp = make_response(render_template("js/config.js.jinja", configs=configs))
    resp.mimetype = "application/javascript"
    return resp
