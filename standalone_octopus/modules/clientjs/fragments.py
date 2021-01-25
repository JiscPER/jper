from flask import Blueprint, abort, render_template

from standalone_octopus.core import app
from standalone_octopus.lib import plugin

blueprint = Blueprint('fragments', __name__)

@blueprint.route("/<frag_id>")
def fragment(frag_id):
    cfg = app.config.get("FRAGMENTS", {}).get(frag_id)
    if cfg is None:
        abort(404)

    # see if we want to render from a function
    fname = cfg.get("function")
    if fname is not None:
        fn = plugin.load_function(fname)
        return fn()

    # see if we want to render from a template
    temp = cfg.get("template")
    if temp is not None:
        return render_template(temp)

    abort(404)
