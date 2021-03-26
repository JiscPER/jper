"""
Blueprint for providing test endpoints for when the system is run in functional test mode.

Under normal operation, this blueprint will not be in use
"""
from flask import Blueprint, send_from_directory
from octopus.lib import paths

blueprint = Blueprint('test', __name__)

@blueprint.route("/download/<filename>", methods=["GET"])
def download(filename):
    """
    Provide a binary file to download under any filename.

    This allows test infrastructure to use this endpoint as a source of arbitrary external binary content
    for the purposes of integrating that functionality into a test

    :param filename:
    :return:
    """
    resources = paths.rel2abs(__file__, "..", "tests", "resources")
    return send_from_directory(resources, "download.pdf")