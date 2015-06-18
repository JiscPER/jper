from flask import Blueprint, send_from_directory
from octopus.lib import paths

blueprint = Blueprint('test', __name__)

@blueprint.route("/download/<filename>", methods=["GET"])
def download(filename):
    resources = paths.rel2abs(__file__, "..", "tests", "resources")
    return send_from_directory(resources, "download.pdf")